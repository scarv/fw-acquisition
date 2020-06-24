
#include <stdlib.h>
#include <string.h>

#include "scass_target.h"


/*!
@brief Send the name of the experiment to the host.
@details Writes a single byte indicating the length of the experiment
name string, followed by experiment name string.
@returns void
*/
static void get_experiment_name(
    scass_target_cfg * cfg
) {
    
    int len = strlen(cfg -> experiment_name);

    uint8_t namelen = len&0xFF;

    cfg -> scass_io_wr_char(namelen);

    for(int i = 0; i < namelen; i ++) {
        
        cfg -> scass_io_wr_char(cfg -> experiment_name[i]);

    }

}


/*!
@brief write a 32-bit integer to the UART
@note Writes least significant byte first.
*/
static void dump_uint32(
    scass_target_cfg * cfg,
    uint32_t data
) {
    cfg -> scass_io_wr_char((data >> 24)&0xFF);
    cfg -> scass_io_wr_char((data >> 16)&0xFF);
    cfg -> scass_io_wr_char((data >>  8)&0xFF);
    cfg -> scass_io_wr_char((data >>  0)&0xFF);
}


/*!
@brief Dump the supplied bytes to the UART
*/
static void dump_bytes (
    scass_target_cfg * cfg  ,
    char             * data ,
    size_t             count
) {
    for(size_t i = 0; i < count; i ++) {
        cfg -> scass_io_wr_char(data[i]);
    }
}


//! Read a 32-bit integer from the UART.
static uint32_t read_uint32 (
    scass_target_cfg * cfg
) {
    uint32_t recv  = ((uint32_t)cfg -> scass_io_rd_char() <<  0);
             recv |= ((uint32_t)cfg -> scass_io_rd_char() <<  8);
             recv |= ((uint32_t)cfg -> scass_io_rd_char() << 16);
             recv |= ((uint32_t)cfg -> scass_io_rd_char() << 24);
    return recv;
}


/*!
@brief Dump a serialised version of a variable struct to the UART
@returns Zero if successful. non-zero otherwise.
*/
static int dump_variable_info (
    scass_target_cfg * cfg
) {
    uint8_t          var_idx = cfg -> scass_io_rd_char();

    if(var_idx > cfg -> num_variables) {
        return 1;
    }

    scass_target_var var     = cfg -> variables[var_idx];

    uint32_t         namelen = strlen(var.name);

    dump_uint32(cfg, namelen);
    dump_uint32(cfg, var.size);
    dump_uint32(cfg, var.flags);
    dump_bytes (cfg, var.name , namelen );

    return 0;
}


/*!
@brief Dump a serialised version of a variable value.
@returns Zero if successful. non-zero otherwise.
*/
static int dump_variable_value (
    scass_target_cfg * cfg,
    char               fixed
) {
    uint8_t          var_idx = cfg -> scass_io_rd_char();

    if(var_idx > cfg -> num_variables) {
        return 1;
    }

    scass_target_var var     = cfg -> variables[var_idx];

    char * todump = fixed ? (char*)var.fixed_value : (char*)var.value;

    dump_bytes(cfg, todump, var.size);

    return 0;
}


/*!
@brief Set the value of a variable based on data read from the UART.
@note Assumes you know the exact size in bytes of the variable, and that
the correct number of bytes will be recieved via the UART.
@returns Zero if successful. non-zero otherwise.
*/
static int set_variable_value (
    scass_target_cfg * cfg,
    char               fixed
) {
    uint8_t          var_idx = cfg -> scass_io_rd_char();

    if(var_idx > cfg -> num_variables) {
        return 1;
    }

    scass_target_var var     = cfg -> variables[var_idx];
    
    char * toset = fixed ? (char*)var.fixed_value : (char*)var.value;

    for(unsigned int i = 0; i < var.size; i ++) {
        toset[i] = cfg -> scass_io_rd_char();
    }

    return 0;
}


/*!
@brief Recieves cfg -> randomness_len bytes from the UART and uses them to
    seed the onboard randomness.
@returns 0
*/
static int seed_randomness (
    scass_target_cfg * cfg
) {

    for(unsigned int i = 0; i < cfg -> randomness_len; i ++) {
        cfg -> randomness[i] = cfg -> scass_io_rd_char();
    }

    return 0;

}


/*!
@brief Reads 4 bytes from the UART (little endian) and turns this into
 an address. It then Jumps to this address without returning.
*/
void do_goto(scass_target_cfg * cfg) {

    void (*func)();

    uint32_t target = read_uint32(cfg);

    func = (void(*)())target;

    func();

    __builtin_unreachable();
}

//! Run a single fixed / random experiment.
static int run_experiment (
    scass_target_cfg * cfg,
    char                fixed
){
                
    if(cfg -> scass_experiment_pre_run != NULL) {
        cfg -> scass_experiment_pre_run(cfg,fixed);
    }
    
    int failure = cfg -> scass_experiment_run(cfg,fixed);
    
    if(cfg -> scass_experiment_post_run != NULL) {
        cfg -> scass_experiment_post_run(cfg,fixed);
    }

    return failure;

}


/*!
@brief Send the clock information for the target back to the host.
*/
static int do_get_clk_info (
    scass_target_cfg      * cfg,  //!< The target configuration.
    scass_target_clk_info * clk   //!< The clock to send info about
) {
    // First, write a 1-byte value representing the number of
    // different system clock rates possible.
    cfg -> scass_io_wr_char(clk -> clk_rates_num);

    // For each system clock rate, send a 4-byte value to the host
    // representing that rate in hertz.
    for(uint8_t i = 0; i < clk -> clk_rates_num; i ++) {
        dump_uint32(cfg, clk -> clk_rates[i]);
    }

    // Send the current clock rate.
    dump_uint32(cfg, clk -> clk_current);
    
    // Send the external clock rate.
    dump_uint32(cfg, clk -> clk_current);

    // Send the current clock source - encoded as 1 byte.
    cfg -> scass_io_wr_char(clk -> clk_source_current   );
    
    // Send the available clock sources - encoded as 1 byte bitfield.
    cfg -> scass_io_wr_char(clk -> clk_source_avail     );

    return 0;
}


//! Set current system clock information.
static int do_set_clk_info (
    scass_target_cfg * cfg
) {
    uint32_t    ext_rate = read_uint32(cfg);
    uint32_t    clk_rate = read_uint32(cfg);
    
    scass_clk_src_t src  = cfg -> scass_io_rd_char();

    cfg -> sys_clk.ext_clk_rate = ext_rate;
    cfg -> sys_clk.sys_set_clk_rate(clk_rate, src, &cfg -> sys_clk);

    return 0;
}

void scass_loop (
    scass_target_cfg * cfg
) {

    while(1) {

        uint8_t cmd = cfg -> scass_io_rd_char();
        uint8_t success = 1;
        uint8_t rsp = SCASS_RSP_ERROR;

        switch(cmd) {
            case SCASS_CMD_HELLOWORLD:
                success = 0;
                break;

            case SCASS_CMD_INIT_EXPERIMENT:
                success = cfg -> scass_experiment_init(cfg);
                break;

            case SCASS_CMD_RUN_FIXED:
                success  = run_experiment(cfg,1);
                break;
            
            case SCASS_CMD_RUN_RANDOM:
                success  = run_experiment(cfg,0);
                break;

            case SCASS_CMD_EXPERIMENT_NAME:
                get_experiment_name(cfg);
                success = 0;
                break;

            case SCASS_CMD_GET_CYCLES:
                dump_uint32(cfg, cfg -> experiment_cycles);
                success = 0;
                break;

            case SCASS_CMD_GET_INSTRRET:
                dump_uint32(cfg, cfg -> experiment_instrret);
                success = 0;
                break;
            
            case SCASS_CMD_GOTO:
                do_goto(cfg); // Does not return.
                __builtin_unreachable();
                break;

            case SCASS_CMD_GET_VAR_NUM:
                cfg -> scass_io_wr_char(cfg -> num_variables);
                success = 0;
                break;

            case SCASS_CMD_GET_VAR_INFO:
                success = dump_variable_info(cfg);
                break;

            case SCASS_CMD_GET_VAR_VALUE:
                success = dump_variable_value(cfg,0);
                break;
            
            case SCASS_CMD_SET_VAR_VALUE:
                success = set_variable_value(cfg,0);
                break;
            
            case SCASS_CMD_GET_VAR_FIXED:
                success = dump_variable_value(cfg,1);
                break;
            
            case SCASS_CMD_SET_VAR_FIXED:
                success = set_variable_value(cfg,1);
                break;

            case SCASS_CMD_RAND_GET_LEN:
                dump_uint32(cfg, cfg -> randomness_len);
                success = 0;
                break;

            case SCASS_CMD_RAND_GET_INTERVAL:
                dump_uint32(cfg, cfg -> randomness_refresh_rate);
                success = 0;
                break;

            case SCASS_CMD_RAND_SEED:
                success = seed_randomness(cfg);
                break;

            case SCASS_CMD_GET_CLK_INFO:
                success = do_get_clk_info(cfg, &cfg -> sys_clk);
                break;

            case SCASS_CMD_SET_SYS_CLK:
                success = do_set_clk_info(cfg);
                break;

            default:
                break;
        }

        rsp = success ? SCASS_RSP_ERROR : SCASS_RSP_OKAY;

        if(rsp == SCASS_RSP_ERROR) {
        
            cfg -> scass_io_wr_char(rsp);
            cfg -> scass_io_wr_char(cmd);
        }

    }

    __builtin_unreachable();

}

/*!
*/
void scass_debug_str(
    scass_target_cfg * cfg, //!< The config to debug with
    char             * str
){
    size_t len = strlen(str);

    cfg -> scass_io_wr_char(SCASS_RSP_DEBUG);

    dump_bytes(cfg, str, len);

    cfg -> scass_io_wr_char('\n');
}

