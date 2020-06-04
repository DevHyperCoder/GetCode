import string
import random

from getcode.utils import does_snippet_exist

def get_rand_base64():
    base64chars=string.digits+string.ascii_letters+'_'+'-'
    rand_id =  ''.join((random.choice(base64chars) for i in range(10)))

    if does_snippet_exist(snippet_id=rand_id):
        rand_id = get_rand_base64()

    return rand_id
