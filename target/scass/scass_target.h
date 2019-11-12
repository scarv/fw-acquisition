
#include <stdint.h>

#ifndef SCASS_TARGET_H
#define SCASS_TARGET_H

#define SCASS_CMD_HELLOWORLD            'H'
#define SCASS_CMD_INIT_EXPERIMENT       'I'
#define SCASS_CMD_RUN_EXPERIMENT        'R'
#define SCASS_CMD_EXPERIMENT_NAME       'N'
#define SCASS_CMD_GOTO                  'G'
#define SCASS_CMD_GET_CYCLES            'C'
#define SCASS_CMD_GET_INSTRRET          'E'
#define SCASS_CMD_GET_VAR_NUM           'V'
#define SCASS_CMD_GET_VAR_INFO          'D'
#define SCASS_CMD_GET_VAR_VALUE         '1'
#define SCASS_CMD_SET_VAR_VALUE         '2'

#define SCASS_RSP_OKAY            '0'
#define SCASS_RSP_ERROR           '!'

#define SCASS_FLAG_RANDOMISE (0x1 << 0)
#define SCASS_FLAG_INPUT     (0x1 << 1)
#define SCASS_FLAG_OUTPUT    (0x1 << 2)
#define SCASS_FLAG_TTEST_VAR (0x1 << 3)

/*!
@brief Describes a single input/output variable for a SCASS managed experiment.
*/
typedef struct __scass_target_var scass_target_var;
struct __scass_target_var {
    
    //! Friendly name of the variable.
    char   * name;
    
    //! Size in bytes of the variable.
    uint32_t size;

    //! Pointer to the data representing the variable.
    void   * value;
    
    //! Single bit status flags.
    uint32_t flags;

};


/*!
@brief Configuration object used to setup a scass target platform.
@details Contains Information about the platform, analysis function
pointers and data containers.
*/
typedef struct __scass_target_cfg scass_target_cfg;
struct __scass_target_cfg {

    //! The name of the experiment currently under analysis.
    char * experiment_name;
    
    /*! @brief An array of variables used in the experiment which the SCASS
           framework has access too. */
    scass_target_var * variables;
    
    //! The number of variables in this target configuration.
    uint8_t   num_variables;

    //! The number of cycles taken to execute 1 iteration of the experiment.
    uint32_t  experiment_cycles;
    
    //! The number of instructions retired in 1 iteration of the experiment.
    uint32_t  experiment_instrret;

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
    @brief Automatically called before every experiment run.
    @param cfg - The scass_target_cfg object associated with the experiment.
    @returns 0 on success, non-zero on failure.
    */
    uint8_t (*scass_experiment_pre_run)(
        scass_target_cfg * cfg
    );
    
    /*!
    @brief Run the experiment once.
    @details May be set to NULL, in which case it is never called.
    @param cfg - The scass_target_cfg object associated with the experiment.
    @returns 0 on success, non-zero on failure.
    */
    uint8_t (*scass_experiment_run)(
        scass_target_cfg * cfg
    );
    
    /*!
    @brief Automatically called after every experiment run.
    @details May be set to NULL, in which case it is never called.
    @param cfg - The scass_target_cfg object associated with the experiment.
    @returns 0 on success, non-zero on failure.
    */
    uint8_t (*scass_experiment_post_run)(
        scass_target_cfg * cfg
    );

};



/*!
@brief The main control loop for the scass target.
@details Continually loops waiting for commands from the host.
@note This function does not return.
*/
void scass_loop(
    scass_target_cfg * cfg //!< The config to run with.
);

#endif
