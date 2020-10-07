
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
    scass_target_cfg      * cfg   //!< The target configuration.
) {
    // First, write a 1-byte value representing the number of
    // different system clock rates possible.
    cfg -> scass_io_wr_char(cfg -> num_clk_cfgs);

    // Next, write a byte indicating the current clock rate.
    cfg -> scass_io_wr_char(cfg -> current_clk_cfg);

    // For each system clock rate, send a 4-byte value to the host
    // representing that rate in hertz, followed by a 1-byte value
    // indicating the clock source.
    for(uint8_t i = 0; i < cfg -> num_clk_cfgs ; i ++) {
        
        // send clock rate
        dump_uint32(cfg, cfg -> clk_cfgs[i].sys_clk_rate);
        
        // send clock source
        cfg -> scass_io_wr_char(cfg -> clk_cfgs[i].sys_clk_src);
    }

    return 0;
}


//! Set current system clock information.
static int do_set_clk_info (
    scass_target_cfg * cfg
) {
    uint8_t cfg_num = cfg -> scass_io_rd_char(cfg);

    cfg -> sys_set_clk_rate(cfg_num, cfg);

    return 0;
}

void __scass_set_panic_handler();

asm (
".global __scass_set_panic_handler  \n"
"__scass_set_panic_handler:  \n"
"    la a0, __scass_panic  \n"
"    csrw mtvec, a0  \n"
"    ret  \n"
"  \n"
".balign 4  \n"
".global __scass_panic  \n"
"__scass_panic:  \n"
"    j scass_panic  \n"
);

    
scass_target_cfg * pcfg;


static const char lut []= "0123456789ABCDEF";

//! Print a 32-bit number as hex
void puthex32(uint32_t w) {
    for(int i =  3; i >= 0; i --) {
        pcfg -> scass_io_wr_char(lut[(w >> (8*i + 4)) & 0xF]);
        pcfg -> scass_io_wr_char(lut[(w >> (8*i    )) & 0xF]);
    }
}

//! Trap handler to dump information to the UART on an exception.
void scass_panic() {
    uint32_t mepc, mstatus, mtval, mcause, sp, ra;

    asm volatile("mv   %0, sp       " : "=r"(sp     ));
    asm volatile("mv   %0, ra       " : "=r"(ra     ));
    asm volatile("csrr %0, mepc     " : "=r"(mepc   ));
    asm volatile("csrr %0, mstatus  " : "=r"(mstatus));
    asm volatile("csrr %0, mtval    " : "=r"(mtval  ));
    asm volatile("csrr %0, mcause   " : "=r"(mcause ));
    char nl = '\n';
    pcfg -> scass_io_wr_char(nl);
    pcfg -> scass_io_wr_char('p');
    pcfg -> scass_io_wr_char('a');
    pcfg -> scass_io_wr_char('n');
    pcfg -> scass_io_wr_char('i');
    pcfg -> scass_io_wr_char('c');
    pcfg -> scass_io_wr_char(nl);

    puthex32(mepc   ); pcfg -> scass_io_wr_char(nl);
    puthex32(mstatus); pcfg -> scass_io_wr_char(nl);
    puthex32(mtval  ); pcfg -> scass_io_wr_char(nl);
    puthex32(mcause ); pcfg -> scass_io_wr_char(nl);
    puthex32(sp     ); pcfg -> scass_io_wr_char(nl);
    puthex32(ra     ); pcfg -> scass_io_wr_char(nl);

    while(1) {}

    __builtin_unreachable();
}


void scass_loop (
    scass_target_cfg * cfg
) {
    pcfg = cfg;

    __scass_set_panic_handler();

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
                success = do_get_clk_info(cfg);
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
    // EMPTY
}

