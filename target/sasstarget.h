
/*!
@brief Top level header file for the sass target.
@details Contains common definitions and data types.
*/

#ifndef SASSTARGET_H
#define SASSTARGET_H

//
// Command codes for communicating with the target
//
static const unsigned char SASS_CMD_HELLOWORLD = 0x01
static const unsigned char SASS_CMD_SET_KEY    = 0x02
static const unsigned char SASS_CMD_GET_KEY    = 0x03
static const unsigned char SASS_CMD_SET_MSG    = 0x04
static const unsigned char SASS_CMD_GET_MSG    = 0x05
static const unsigned char SASS_CMD_SET_CIPHER = 0x06
static const unsigned char SASS_CMD_GET_CIPHER = 0x07
static const unsigned char SASS_CMD_SET_CFG    = 0x08
static const unsigned char SASS_CMD_GET_CFG    = 0x09
static const unsigned char SASS_CMD_DO_ENCRYPT = 0x0A
static const unsigned char SASS_CMD_DO_DECRYPT = 0x0B

//
// Status codes for checking if commands all worked.
//
static const unsigned char SASS_STATUS_OK      = 0xA0
static const unsigned char SASS_STATUS_ERR     = 0xFA



/*!
@brief Context object which is used by the environment to configure
the communications and capabilities of the target.
*/
typedef struct {
    
    //! Pointer to function used to send bytes to the host.
    void (*send_byte_to_host)(char to_send);
    
    //! Pointer to function used to recieve bytes from the host.
    char (*recv_byte_from_host)();
    
    //! If set to non-zero, the target will shut down.
    char exit = 0;

} sass_ctx;


/*!
@brief Start running the target program with the supplied context object.
*/
void sass_target_run(
    sass_ctx * ctx
);

#endif
