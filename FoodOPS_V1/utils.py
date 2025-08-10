from typing import Callable


def get_input(
    input_message: str,
    fn_validation: Callable,
    error_message: str = "Erreur dans la saisie",
):
    """Prompt for an integer with validation.

    - input_message: prompt shown to the user
    - fn_validation: predicate taking the parsed int and returning True if valid
    - error_message: message displayed on invalid input
    """
    while True:
        try:
            result = int(input(input_message).strip())
            if fn_validation(result):
                return result
        except Exception:
            pass
        print(error_message)
