import requests
from django.conf import settings
from requests.exceptions import RequestException


def send_sms(phone, message):
    """
    Send SMS using TextBee API.
    This function sends the entire message as one payload to the TextBee API.
    TextBee/SMS gateway will handle any necessary message segmentation if it exceeds
    standard SMS character limits.

    Args:
        phone: Recipient phone number
        message: Message content
    Returns:
        dict: Response containing status and details
    """
    url = f"https://api.textbee.dev/api/v1/gateway/devices/{settings.TEXTBEE_DEVICE_ID}/send-sms"

    headers = {
        "x-api-key": settings.TEXTBEE_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "recipients": [phone],
        "message": message
    }

    try:
        # Debug logging: Shows the API endpoint and the payload being sent
        print(f"TextBee API Request: {url}")
        print(f"Payload: {payload}")

        # Make the POST request to the TextBee API
        # Set a timeout to prevent the request from hanging indefinitely
        response = requests.post(url, json=payload, headers=headers, timeout=10)

        # Debug logging: Shows the HTTP status code and the raw response text
        print(f"Response: {response.status_code} - {response.text}")

        # Raise an HTTPError for bad responses (4xx or 5xx status codes)
        response.raise_for_status()

        # Return success status and the API response data
        return {
            'status': 'success',
            'data': response.json(),
            'device_id': settings.TEXTBEE_DEVICE_ID,
            'chunked_by_local_code': False # Explicitly state that our code did not perform chunking
        }

    except RequestException as e:
        # Catch any request-related exceptions (e.g., network issues, timeouts, HTTP errors)
        return _handle_sms_error(e)


def _handle_sms_error(e):
    """
    Helper function to handle SMS sending errors and format the error response.

    Args:
        e (requests.exceptions.RequestException): The exception object caught during the request.
    Returns:
        dict: A dictionary containing error status and details.
    """
    error_info = {
        'status': 'error',
        'message': str(e), # General error message from the exception
        'device_id': settings.TEXTBEE_DEVICE_ID
    }

    # If the exception has a response attribute (e.g., for HTTP errors)
    if hasattr(e, 'response') and e.response is not None:
        try:
            # Attempt to parse the response body as JSON
            error_info['api_response'] = e.response.json()
        except ValueError:
            # If JSON parsing fails, store the raw text response
            error_info['api_response'] = e.response.text
        # Store the HTTP status code from the response
        error_info['status_code'] = e.response.status_code

    # Debug logging: Prints the detailed error information
    print(f"SMS Error: {error_info}")
    return error_info