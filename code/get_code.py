from utils.temp_mail import wait_for_verification_code


if __name__ == '__main__':
    import sys

    email = sys.argv[1] if len(sys.argv) > 1 else 'testb01@mailto.plus'
    code, mail_id = wait_for_verification_code(email, timeout=30)
    if code:
        print(f'CODE:{code}')
    else:
        print('CODE:None')
