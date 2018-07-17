
"""
This file contains functions and classes which can be used to generate
messages, keys and ciphertexts.
"""

import os
import sys
import random
import secrets
import logging as log

class SassEncryption:
    """
    Module of SASS responsible for generating and maipulating encryption
    artifacts.
    """

    def __init__(self):
        """
        Create a new SassEncryption class instance.
        """


    def GenerateMessage(self, length = 16):
        """
        Generate and return a random plaintext message of the requested
        length.
        - length : Number of bytes in the message.
        Returns a byte string.
        """
        assert type(length) is int, "Message length must be an integer"
        assert length > 0, "Message length must be greater than zero"
        return secrets.token_bytes(nbytes=length)


    def GenerateKeyBits(self, size = 16):
        """
        Generate and return a random cipherkey of the requested size.
        - size : Number of bytes in the key.
        Returns a byte string.
        """
        assert size % 8 == 0, "Key length must be a multiple of 8 bits"
        assert type(size) is int, "Key length must be an integer"
        assert size > 0, "Key length must be greater than zero"
        return secrets.token_bytes(nbytes=size)
