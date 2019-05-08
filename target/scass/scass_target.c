
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


//! Prints hello world as a response to the host.
static void helloworld(
    scass_target_cfg * cfg //!< The scass target config
) {

    char * tosend = "Hello World!\n";

    for(int i = 0; tosend[i] != 0; i++) {

        cfg -> scass_io_wr_char(tosend[i]);

    }

}


uint32_t scass_prng_sample (
    scass_target_cfg * cfg
){
    cfg -> prng_value ^= cfg -> prng_value << 13;
    cfg -> prng_value ^= cfg -> prng_value >> 17;
    cfg -> prng_value ^= cfg -> prng_value <<  5;

    return cfg -> prng_value;
}


void scass_loop (
    scass_target_cfg * cfg
) {

    while(1) {

        uint8_t cmd = cfg -> scass_io_rd_char();
        uint8_t rsp = SCASS_RSP_ERROR;

        switch(cmd) {
            case SCASS_CMD_HELLOWORLD:
                helloworld(cfg);
                rsp = SCASS_RSP_OKAY;
                break;

            case SCASS_CMD_INIT_EXPERIMENT:
                rsp = cfg -> scass_experiment_init(cfg)? SCASS_RSP_ERROR :
                                                         SCASS_RSP_OKAY  ;
                break;

            case SCASS_CMD_RUN_EXPERIMENT:
                rsp = cfg -> scass_experiment_run(cfg) ? SCASS_RSP_ERROR :
                                                         SCASS_RSP_OKAY  ;
                break;

            case SCASS_CMD_SEED_PRNG:
                rsp = seed_prng(cfg) ? SCASS_RSP_ERROR : SCASS_RSP_OKAY;
                break;

            default:
                break;
        }
        
        cfg -> scass_io_wr_char(rsp);

    }

}

