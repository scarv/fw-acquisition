
#include <stdint.h>

#ifndef SCASS_TARGET_H
#define SCASS_TARGET_H

#define SCASS_CMD_HELLOWORLD            'H'
#define SCASS_CMD_INIT_EXPERIMENT       'I'
#define SCASS_CMD_RUN_EXPERIMENT        'R'
#define SCASS_CMD_SEED_PRNG             'P'
#define SCASS_CMD_EXPERIMENT_NAME       'N'
#define SCASS_CMD_EXPERIMENT_LEN_DATA   'L'
#define SCASS_CMD_EXPERIMENT_SET_DATA   'S'
#define SCASS_CMD_EXPERIMENT_GET_DATA   'G'

#define SCASS_RSP_OKAY            '0'
#define SCASS_RSP_ERROR           '!'

/*!
@brief Configuration object used to setup a scass target platform.
@details Contains Information about the platform, analysis function
pointers and data containers.
*/
typedef struct __scass_target_cfg scass_target_cfg;
struct __scass_target_cfg {

    //! The name of the experiment currently under analysis.
    char * experiment_name;
    
    //! Current value of the PRNG.
    uint32_t prng_value;

    //! A buffer of data used to get data in/out of the experiment.
    uint8_t * experiment_data;
    
    //! The length in bytes of the experiments data array.
    uint32_t  experiment_data_len;

    /*!
    @brief Read a single character from the target UART port.
    @warning This function will *block* until a character is recieved.
    @returns The recieved character.
    @details This function must point to a target-defined implementation
    of the IO function.
    */
    uint8_t (*scass_io_rd_char)();

    /*!
    @brief Write a single character to the target UART port.
    @warning This function will *block* until the character is sent.
    @returns void
    @details This function must point to a target-defined implementation
    of the IO function.
    */
    void (*scass_io_wr_char)(uint8_t tosend);

    /*!
    @brief Do any one-time setup needed for the experiment.
    @param cfg - The scass_target_cfg object associated with the experiment.
    @returns 0 on success, non-zero on failure.
    */
    uint8_t (*scass_experiment_init)(
        scass_target_cfg * cfg
    );
    
    /*!
    @brief Run the experiment once.
    @param cfg - The scass_target_cfg object associated with the experiment.
    @returns 0 on success, non-zero on failure.
    */
    uint8_t (*scass_experiment_run)(
        scass_target_cfg * cfg
    );

};


/*!
@brief Update and sample the PRNG associated with the scass target cfg
@returns a 32-bit pseudo random value.
*/
uint32_t scass_prng_sample(
    scass_target_cfg * cfg
);


/*!
@brief The main control loop for the scass target.
@details Continually loops waiting for commands from the host.
@note This function does not return.
*/
void scass_loop(
    scass_target_cfg * cfg //!< The config to run with.
);

#endif
