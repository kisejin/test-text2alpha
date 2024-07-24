def prompt_error_template1(errors: list):
    """Returns a prompt for correctly the error."""
    root_error = errors[0]

    show_error = f"{root_error[0]}. This error occurs in the following function:{root_error[1]}\nError location: {root_error[-1]}"

    if (
        "an unexpected keyword argument" in root_error[0]
        or "module 'backtrader" in root_error[0]
        or "not enough values to unpack" in root_error[0]
    ):

        return f"""
        With the `ERROR MESSEAGE` {show_error}.\n I refer you ignore the indicator by Backtrader package, instead that generate custom indicator following the given descriptions.
        """

    else:
        return f"""
        The code must avoid the {show_error}. Generate custom indicator following the given descriptions."""


def prompt_error_template2(errors: list):
    """Returns a prompt for correctly the error."""
    root_error = errors[0]
    my_code_error = errors[-1]

    show_error = f"{root_error[0]}. This error occurs in the following function:{root_error[1]}\nError location: {root_error[-1]}"

    if (
        "an unexpected keyword argument" in root_error[0]
        or "module 'backtrader" in root_error[0]
        or "not enough values to unpack" in root_error[0]
    ):

        return f"""
        With the `ERROR MESSEAGE` {show_error}.\n I refer you ignore the indicator by Backtrader package, instead that generate custom indicator following the given descriptions.
        """

    return f"""
    You encountered an error from the package `ERROR MESSEAGE`: {root_error[0]} at {root_error[1]}. 
    The error originates from your answer code:\n {my_code_error[0]}\nThe error occurs at location {my_code_error[-1]} of your code answer. The code must not contain this error. Please retry generate custom indicator following the given descriptions."
    """


def prompt_error_template(errors: list, include_my_code_error: bool = False):
    """
    Returns a prompt for correctly the error.
    If include_my_code_error is True, it includes the user's code error in the prompt.
    """
    root_error = errors[0]
    my_code_error = errors[-1] if include_my_code_error else None

    show_error = f"{root_error[0]}. This error occurs in the following function: {root_error[1]}. Error location: {root_error[-1]}"

    error_message = "ERROR MESSAGE"
    # base_prompt = f"With the `{error_message}` {show_error}.\n"
    base_prompt = f"With the error {show_error}"

    if any(
        keyword in root_error[0]
        for keyword in [
            "an unexpected keyword argument",
            "module 'backtrader",
            "not enough values to unpack",
        ]
    ):
        advice = "I recommend ignoring the indicator by the Backtrader package, instead generate a custom indicator following the given descriptions."
    else:
        if (
            include_my_code_error
            and "self.cerebro.run()" not in my_code_error[-1]
        ):
            # advice = f"You encountered an error from the package `{error_message}`: {root_error[0]} at {root_error[1]}\n Error package location {root_error[-1]}: . The error originates from your answer code:\n {my_code_error[0]} and  occurs at location {my_code_error[-1]} of your code answer. The code must avoid this error."
            advice = f"<ERROR> You encountered an error from the package {root_error[0]} at {root_error[1]}. Error package at location: {root_error[-1]}. The error originates from your answer code: {my_code_error[0]} and  occurs at location {my_code_error[-1]} of your code answer</ERROR>. The code must avoid this error."
            return advice
        else:
            # advice = "The code must avoid this error. Generate a custom indicator following the given descriptions."
            advice = "The code must avoid this error."

    return f"<ERROR>{base_prompt}</ERROR>. {advice}"
