
#include <stdlib.h>
#include <string.h>

#include "scass_target.h"


/*!
@brief Read 4 bytes from the UART and use them to seed the PRNG.
@details Reads the most significant byte of the 32-bit seed value first.
@returns 0 on success, non-zero on failure.
*/
static uint8_t seed_prng(
    scass_target_cfg * cfg //!< The scass target config
) {
    
    cfg -> prng_value = (cfg -> scass_io_rd_char() << 24) |
                        (cfg -> scass_io_rd_char() << 16) |
                        (cfg -> scass_io_rd_char() <<  8) |
                        (cfg -> scass_io_rd_char() <<  0) ;

    return 0;

}


uint32_t scass_prng_sample (
    scass_target_cfg * cfg
){
    cfg -> prng_value ^= cfg -> prng_value << 13;
    cfg -> prng_value ^= cfg -> prng_value >> 17;
    cfg -> prng_value ^= cfg -> prng_value <<  5;

    return cfg -> prng_value;
}

/*!
@brief Send the name of the experiment to the host.
@details Writes a single byte indicating the length of the experiment
name string, followed by experiment name string.
@returns 0 on sucess, non-zero on failure.
*/
static uint8_t get_experiment_name(
    scass_target_cfg * cfg
) {
    
    int len = strlen(cfg -> experiment_name);

    uint8_t namelen = len&0xFF;

    cfg -> scass_io_wr_char(namelen);

    for(int i = 0; i < namelen; i ++) {
        
        cfg -> scass_io_wr_char(cfg -> experiment_name[i]);

    }

    return 0;

}


/*!
@brief write a 32-bit integer to the UART representing the length in
  bytes of the experiment data array.
@note Writes least significant byte first.
*/
static uint8_t get_experiment_data_len(
    scass_target_cfg * cfg,
    uint32_t data_len
) {
    uint8_t b0 = (data_len >> 24)&0xFF;
    uint8_t b1 = (data_len >> 16)&0xFF;
    uint8_t b2 = (data_len >>  8)&0xFF;
    uint8_t b3 = (data_len >>  0)&0xFF;

    cfg -> scass_io_wr_char(b0);
    cfg -> scass_io_wr_char(b1);
    cfg -> scass_io_wr_char(b2);
    cfg -> scass_io_wr_char(b3);

    return 0;
}


/*!
@brief Dump the experiment data array to the UART.
*/
static uint8_t get_experiment_data (
    scass_target_cfg * cfg,
    uint32_t           data_len,
    uint8_t          * data_array
) {
    for(int i = 0; i < data_len; i++) {

        cfg -> scass_io_wr_char(data_array[i]);

    }

    return 0;
}


/*!
@brief Set the experiment data content by reading from the UART
*/
static uint8_t set_experiment_data (
    scass_target_cfg * cfg,
    uint32_t           data_len,
    uint8_t          * data_array
) {
    for(int i = 0; i < data_len; i++) {

        data_array[i] = cfg -> scass_io_rd_char();

    }

    return 0;
}


/*!
@brief Reads 4 bytes from the UART (little endian) and turns this into
 an address. It then Jumps to this address without returning.
*/
__attribute__((noreturn))
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
                success = cfg -> scass_experiment_run(cfg);
                break;

            case SCASS_CMD_SEED_PRNG:
                success = seed_prng(cfg);
                break;

            case SCASS_CMD_EXPERIMENT_NAME:
                success = get_experiment_name(cfg);
                break;

            case SCASS_CMD_GET_DATA_IN_LEN:
                success = get_experiment_data_len(cfg,cfg->data_in_len);
                break;
            
            case SCASS_CMD_GET_DATA_OUT_LEN:
                success = get_experiment_data_len(cfg,cfg->data_out_len);
                break;

            case SCASS_CMD_GET_DATA_IN:
                success = get_experiment_data(
                    cfg, cfg -> data_in_len, cfg -> data_in);
                break;
            
            case SCASS_CMD_GET_DATA_OUT:
                success = get_experiment_data(
                    cfg, cfg -> data_out_len, cfg -> data_out);
                break;

            case SCASS_CMD_SET_DATA_IN:
                success = set_experiment_data(
                    cfg, cfg -> data_in_len, cfg -> data_in);
                break;
            
            case SCASS_CMD_SET_DATA_OUT:
                success = set_experiment_data(
                    cfg, cfg -> data_out_len, cfg -> data_out);
                break;
            
            case SCASS_CMD_GOTO:
                do_goto(cfg); // Does not return.
                __builtin_unreachable();
                break;

            default:
                break;
        }

        rsp = success ? SCASS_RSP_ERROR : SCASS_RSP_OKAY;
        
        cfg -> scass_io_wr_char(rsp);

        if(rsp == SCASS_RSP_ERROR) {
            cfg -> scass_io_wr_char(cmd);
        }

    }

}

