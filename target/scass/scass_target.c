
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
    scass_target_cfg * cfg
) {
    uint8_t          var_idx = cfg -> scass_io_rd_char();

    if(var_idx > cfg -> num_variables) {
        return 1;
    }

    scass_target_var var     = cfg -> variables[var_idx];

    dump_bytes(cfg, (char*)var.value, var.size);

    return 0;
}


/*!
@brief Set the value of a variable based on data read from the UART.
@note Assumes you know the exact size in bytes of the variable, and that
the correct number of bytes will be recieved via the UART.
@returns Zero if successful. non-zero otherwise.
*/
static int set_variable_value (
    scass_target_cfg * cfg
) {
    uint8_t          var_idx = cfg -> scass_io_rd_char();

    if(var_idx > cfg -> num_variables) {
        return 1;
    }

    scass_target_var var     = cfg -> variables[var_idx];

    for(int i = 0; i < var.size; i ++) {
        ((uint8_t*)var.value)[i] = cfg -> scass_io_rd_char();
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

    for(int i = 0; i < cfg -> randomness_len; i ++) {
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

    uint32_t target = ((uint32_t)cfg -> scass_io_rd_char() <<  0) |
                      ((uint32_t)cfg -> scass_io_rd_char() <<  8) |
                      ((uint32_t)cfg -> scass_io_rd_char() << 16) |
                      ((uint32_t)cfg -> scass_io_rd_char() << 24) ;

    func = (void(*)())target;

    func();

    __builtin_unreachable();
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

            case SCASS_CMD_RUN_EXPERIMENT:
                
                if(cfg -> scass_experiment_pre_run != NULL) {
                    cfg -> scass_experiment_pre_run(cfg);
                }
                
                success = cfg -> scass_experiment_run(cfg);

                if(cfg -> scass_experiment_post_run != NULL) {
                    cfg -> scass_experiment_post_run(cfg);
                }

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

            case SCASS_CMD_GET_VAR_INFO:
                success = dump_variable_info(cfg);

            case SCASS_CMD_GET_VAR_VALUE:
                success = dump_variable_value(cfg);
            
            case SCASS_CMD_SET_VAR_VALUE:
                success = set_variable_value(cfg);

            case SCASS_CMD_RAND_GET_LEN:
                dump_uint32(cfg, cfg -> randomness_len);
                success = 0;

            case SCASS_CMD_RAND_SEED:
                success = seed_randomness(cfg);

            default:
                break;
        }

        rsp = success ? SCASS_RSP_ERROR : SCASS_RSP_OKAY;
        
        cfg -> scass_io_wr_char(rsp);

        if(rsp == SCASS_RSP_ERROR) {
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

    cfg -> scass_io_wr_char(str[i]);
}

