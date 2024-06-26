
#include <stdint.h>

#ifndef SCASS_TARGET_H
#define SCASS_TARGET_H

#define SCASS_CMD_HELLOWORLD            'H'
#define SCASS_CMD_INIT_EXPERIMENT       'I'
#define SCASS_CMD_RUN_RANDOM            'R'
#define SCASS_CMD_RUN_FIXED             'F'
#define SCASS_CMD_EXPERIMENT_NAME       'N'
#define SCASS_CMD_GOTO                  'G'
#define SCASS_CMD_GET_CYCLES            'C'
#define SCASS_CMD_GET_INSTRRET          'E'
#define SCASS_CMD_GET_VAR_NUM           'V'
#define SCASS_CMD_GET_VAR_INFO          'D'
#define SCASS_CMD_GET_VAR_VALUE         '1'
#define SCASS_CMD_SET_VAR_VALUE         '2'
#define SCASS_CMD_GET_VAR_FIXED         '3'
#define SCASS_CMD_SET_VAR_FIXED         '4'
#define SCASS_CMD_RAND_GET_LEN          'L'
#define SCASS_CMD_RAND_GET_INTERVAL     'l'
#define SCASS_CMD_RAND_SEED             'S'
#define SCASS_CMD_GET_CLK_INFO          'c'
#define SCASS_CMD_SET_SYS_CLK           'r'

#define SCASS_CLK_SRC_EXTERNAL          0b00000001
#define SCASS_CLK_SRC_INTERNAL          0b00000010
#define SCASS_CLK_SRC_PLL_EXT           0b00000100
#define SCASS_CLK_SRC_PLL_INT           0b00001000

#define SCASS_RSP_OKAY            '0'
#define SCASS_RSP_ERROR           '!'
#define SCASS_RSP_DEBUG           '?'

#define SCASS_FLAG_RANDOMISE (0x1 << 0)
#define SCASS_FLAG_INPUT     (0x1 << 1)
#define SCASS_FLAG_OUTPUT    (0x1 << 2)
#define SCASS_FLAG_TTEST_VAR (0x1 << 3)

#define SCASS_FLAGS_TTEST_IN (SCASS_FLAG_RANDOMISE |\
                              SCASS_FLAG_INPUT     |\
                              SCASS_FLAG_TTEST_VAR )

//! Typedef for a clock source indicator.
typedef uint8_t scass_clk_src_t;

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
    
    //! The fixed value of this variable. Used for TTests.
    void   * fixed_value;
    
    //! Single bit status flags.
    uint32_t flags;

};

/*!
@brief A container for target clocking information.
*/
typedef struct __scass_target_clk_info scass_target_clk_info;
struct         __scass_target_clk_info {
    
    //! System Clock rate
    uint32_t            sys_clk_rate;
    
    //! System clock source: internal/external/pll
    scass_clk_src_t     sys_clk_src;

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

    /*! @brief Array of onboard random data, which is seeded by the host
               but updated thereafter by the target.
    */
    uint8_t * randomness;

    //! Length of the randomness data array.
    uint32_t  randomness_len;
    
    /*!
    @brief Refresh the randomness array every time this many traces have
        been captured.
    @note If set to zero then the randomness is never updated.
    */
    uint32_t  randomness_refresh_rate;
    
    //! Contains information on possible clock rates for the target.
    scass_target_clk_info * clk_cfgs;

    //! Index into the clk_cfgs array, indicating current clock config.
    uint8_t                 current_clk_cfg;
    
    //! Number of clock configurations available.
    uint8_t                 num_clk_cfgs;
    
    /*!
    @brief Function pointer targets provide to set the current clock rate.
    @param in new_clk_cfg - index into cfg.clk_cfgs indicating config to set.
    @param in cfg    - SCASS config object containing new clock config.
    @details Looks a current_clk_cfg and clk_cfgs of cfg.
    @returns void
    */
    void (*sys_set_clk_rate)(
        uint8_t             new_clk_cfg,
        scass_target_cfg *  cfg
    );

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
    @param fixed - Use fixed variants of each variable
    @returns 0 on success, non-zero on failure.
    */
    uint8_t (*scass_experiment_pre_run)(
        scass_target_cfg * cfg,
        char               fixed
    );
    
    /*!
    @brief Run the experiment once.
    @details May be set to NULL, in which case it is never called.
    @param cfg - The scass_target_cfg object associated with the experiment.
    @param fixed - Use fixed variants of each variable
    @returns 0 on success, non-zero on failure.
    */
    uint8_t (*scass_experiment_run)(
        scass_target_cfg * cfg,
        char               fixed
    );
    
    /*!
    @brief Automatically called after every experiment run.
    @details May be set to NULL, in which case it is never called.
    @param cfg - The scass_target_cfg object associated with the experiment.
    @param fixed - Use fixed variants of each variable
    @returns 0 on success, non-zero on failure.
    */
    uint8_t (*scass_experiment_post_run)(
        scass_target_cfg * cfg,
        char               fixed
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


/*!
@brief Print a string to the host using the SCASS debug protocol
@details Sends the SCASS_RSP_DEBUG symbol to the host, followed by
    a null terminated string. The Host will read the string until
    a newline is encountered. The function automatically appends a
    newline ('\n') to the string when sending it.
@param str - The NULL terminated string to print.
*/
void scass_debug_str(
    scass_target_cfg * cfg, //!< The config to debug with
    char             * str
);

#endif
