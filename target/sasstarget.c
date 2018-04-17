
/*!
@brief Code file for the sass target.
@details Implements the functionality needed to communicate with the host.
*/




/*!
@param ctx in - Pointer ot the context object used by the target to call into
the external world and communicate with the host.
*/
void sass_target_run(
    sass_ctx * ctx
) {

    while(ctx -> exit == 0) {

        char input = ctx -> recv_byte_from_host();

        switch(input) {

            case(SASS_CMD_HELLOWORLD):
                // Test command, send the OK response only.
                ctx -> send_byte_to_host(SASS_STATUS_OK);
                break;

            default:
                // By default, send an error response for requests we
                // do not understand.
                ctx -> send_byte_to_host(SASS_STATUS_ERR);
                break;

        }


    }


}
