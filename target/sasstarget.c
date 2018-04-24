
/*!
@brief Code file for the sass target.
@details Implements the functionality needed to communicate with the host.
*/

#include "sasstarget.h"


/*!
@param ctx in - Pointer ot the context object used by the target to call into
the external world and communicate with the host.
*/
void sass_target_run(
    sass_ctx * ctx
) {

    while(ctx -> exit == 0) {

        char input = ctx -> recv_byte_from_host();

        int i;

        if(input == SASS_CMD_HELLOWORLD){
            // Test command, send the OK response only.
            ctx -> send_byte_to_host(SASS_STATUS_OK);


        } else if(input == SASS_CMD_SET_KEY){
            // Read the next SASS_KEY_LENGTH bytes, set the key
            // and return OK
            for(i=0; i < SASS_KEY_LENGTH; i ++) {
                ctx -> key[i] = ctx -> recv_byte_from_host();
            }
            ctx -> send_byte_to_host(SASS_STATUS_OK);

        } else if(input == SASS_CMD_GET_KEY){
            // Write all bytes of the key to the host followed by
            // the OK byte.
            for(i=0; i < SASS_KEY_LENGTH; i ++) {
                ctx -> send_byte_to_host(ctx -> key[i]);
            }
            ctx -> send_byte_to_host(SASS_STATUS_OK);


        } else if(input == SASS_CMD_SET_CIPHER){
            // Read the next SASS_CIPHER_LENGTH bytes, set the key
            // and return OK
            for(i=0; i < SASS_MSG_LENGTH; i ++) {
                ctx -> cipher[i] = ctx -> recv_byte_from_host();
            }
            ctx -> send_byte_to_host(SASS_STATUS_OK);

        } else if(input == SASS_CMD_GET_CIPHER){
            // Write all bytes of the key to the host followed by
            // the OK byte.
            for(i=0; i < SASS_MSG_LENGTH; i ++) {
                ctx -> send_byte_to_host(ctx -> cipher[i]);
            }
            ctx -> send_byte_to_host(SASS_STATUS_OK);


        } else if(input == SASS_CMD_SET_MSG){
            // Read the next SASS_MSG_LENGTH bytes, set the message
            // and return OK
            for(i=0; i < SASS_MSG_LENGTH; i ++) {
                ctx -> message[i] = ctx -> recv_byte_from_host();
            }
            ctx -> send_byte_to_host(SASS_STATUS_OK);

        } else if(input == SASS_CMD_GET_MSG){
            // Write all bytes of the message to the host followed by
            // the OK byte.
            for(i=0; i < SASS_MSG_LENGTH; i ++) {
                ctx -> send_byte_to_host(ctx -> message[i]);
            }
            ctx -> send_byte_to_host(SASS_STATUS_OK);

        } else if(input == SASS_CMD_DO_ENCRYPT) {

            // Perform an encryption, then send the OK response
            // back to the host
            ctx -> encrypt (
                ctx -> message,
                ctx -> key,
                ctx -> cipher,
                SASS_KEY_LENGTH,
                SASS_MSG_LENGTH
            );
            ctx -> send_byte_to_host(SASS_STATUS_OK);

        } else if(input == SASS_CMD_DO_DECRYPT) {

            // Perform a decryption, then send the OK response
            // back to the host
            ctx -> decrypt (
                ctx -> message,
                ctx -> key,
                ctx -> cipher,
                SASS_KEY_LENGTH,
                SASS_MSG_LENGTH
            );
            ctx -> send_byte_to_host(SASS_STATUS_OK);

        } else if(input == SASS_CMD_DO_CUSTOM) {

            // Run the custom command and return the result.
            char tr = ctx -> custom();
            ctx -> send_byte_to_host(tr);

        } else {
            // By default, send an error response for requests we
            // do not understand.
            ctx -> send_byte_to_host(SASS_STATUS_ERR);

        }


    }


}
