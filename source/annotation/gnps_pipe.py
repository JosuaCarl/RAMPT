#!/usr/bin/env python3

"""
Use GNPS for anntating compounds.
"""

# Imports
import warnings
import time
import math
import requests



def main():
    pass



def check_for_str_request(url:str | bytes, query:str, retries:int=100, allowed_fails:int=10, expected_wait_time:float=600.0, verbosity:int=1, **kwargs) -> bool:
    """
    Check the given URL for a given query. The task is retried a number of times with logarithmically (log2) decreasing time between requests after one initial request.

    :param url: Target URL
    :type url: str | bytes
    :param query: Query string that is searched in response
    :type query: str
    :param retries: Number of retries, defaults to 100
    :type retries: int, optional
    :param allowed_fails: Number of times the request are allowed to fail, defaults to 10
    :type allowed_fails: int, optional
    :param expected_wait_time: Expected time until query is found, defaults to 10.0
    :type expected_wait_time: float, optional
    :param verbosity: Level of verbosity, defaults to 1
    :type verbosity: int, optional
    :param kwargs: Additional arguments, passed on to requests.get()
    :type kwargs: any, optional
    :return: Query found ?
    :rtype: bool
    """
    fails = []
    for i in range(retries):
        response = requests.get(url,  **kwargs)
        if response.status_code == 200:
            if query in  str(response.content):
                return True
        else:
            fails.append(response.status_code)
            if verbosity >= 1:
                warnings.warn( f"{url} returned status code {response.status_code} after {i} retries.\
                            Requesting this URL will be terminated after further {allowed_fails - len(fails)} failed requests.",
                            category=UserWarning )
        if len(fails) > allowed_fails:
            raise LookupError(f"The request to {url} failed more than {allowed_fails} times with the following status codes:\n{fails}")
        
        # Retry
        retry_time = ( 1 / math.log2(i + 2) ) * expected_wait_time
        if verbosity >= 2:
            print(f"{query} not found at {url}. Retrying in {retry_time}s.")
        time.sleep(retry_time)
    return False

task_id = "bb679dc3f6cf4383b8c8e58a73b97b39"
url = f"https://gnps.ucsd.edu/ProteoSAFe/status_json.jsp?task={task_id}"
check_for_str_request(url=url, query='\"status\":\"DONE\"', retries=100, allowed_fails=10, wait_time_init=10.0, timeout=5)