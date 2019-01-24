
/*!
@brief Top level header file for the sass target.
@details Contains common definitions and data types.
*/

#ifndef SASSTARGET_H
#define SASSTARGET_H

//
// Command codes for communicating with the target
//
static const unsigned char SASS_CMD_HELLOWORLD = 0x01;
static const unsigned char SASS_CMD_SET_KEY    = 0x02;
static const unsigned char SASS_CMD_GET_KEY    = 0x03;
static const unsigned char SASS_CMD_SET_MSG    = 0x04;
static const unsigned char SASS_CMD_GET_MSG    = 0x05;
static const unsigned char SASS_CMD_SET_CIPHER = 0x06;
static const unsigned char SASS_CMD_GET_CIPHER = 0x07;
static const unsigned char SASS_CMD_SET_CFG    = 0x08;
static const unsigned char SASS_CMD_GET_CFG    = 0x09;
static const unsigned char SASS_CMD_DO_ENCRYPT = 0x0A;
static const unsigned char SASS_CMD_DO_DECRYPT = 0x0B;
static const unsigned char SASS_CMD_DO_CUSTOM  = 0x0C;

//
// Status codes for checking if commands all worked.
//
static const unsigned char SASS_STATUS_OK      = 0xA0;
static const unsigned char SASS_STATUS_ERR     = 0xFA;


//
// Key and message lengths
//
#define SASS_KEY_LENGTH 16 
#define SASS_MSG_LENGTH 16 
#define SASS_CFG_FIELDS 16

typedef struct _sass_ctx_ sass_ctx;

//! Dummy function which does nothing. Used to initialise function pointers.
void _sass_ctx_null_(sass_ctx * ctx);

//! Initialise a new sass context object
void sass_ctx_init(sass_ctx * ctx);

/*!
@brief Context object which is used by the environment to configure
the communications and capabilities of the target.
*/
struct _sass_ctx_ {
    
    //! Pointer to function used to send bytes to the host.
    void (*send_byte_to_host)(unsigned char to_send);
    
    //! Pointer to function used to recieve bytes from the host.
    unsigned char (*recv_byte_from_host)();

    //! Pointer to function used for encryption
    void (*encrypt)(
        char * message,
        char * key,
        char * cipher,
        unsigned int key_len,
        unsigned int msg_len
    );
    
    //! Pointer to function used for decryption
    void (*decrypt)(
        char * message,
        char * key,
        char * cipher,
        unsigned int key_len,
        unsigned int msg_len
    );    
    
    //! A bunch of get/setable switches.
    char    config_fields [SASS_CFG_FIELDS];
    
    //! Pointer to function which implements the "custom" command.
    unsigned char (*custom)();    

    //! Called whenever the message is set to a new value
    void (*on_message_set)(
        sass_ctx * ctx  
    );
    
    //! Called whenever the key is set to a new value
    void (*on_key_set)(
        sass_ctx * ctx  
    );

    //! Called whenever the ciphertext is set to a new value
    void (*on_ciphertext_set)(
        sass_ctx * ctx  
    );

    //! If set to non-zero, the target will shut down.
    char exit;

    //! The current message value.
    char    message [SASS_MSG_LENGTH];

    //! The current cipher text value.
    char    cipher  [SASS_MSG_LENGTH];

    //! The current key value
    char    key     [SASS_KEY_LENGTH];

};


/*!
@brief Start running the target program with the supplied context object.
*/
void sass_target_run(
    sass_ctx * ctx
);

#endif
