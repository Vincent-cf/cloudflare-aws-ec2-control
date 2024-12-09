import hmac
import hashlib
import datetime
import httpx

# AWS region and EC2 instance details
REGION = "eu-west-1"
INSTANCE_ID = "i-01aa59cc2a32995b8"

# Generate AWS Signature Version 4
def generate_aws_signature(key, date_stamp, region_name, service_name, string_to_sign):
    k_date = hmac.new(("AWS4" + key).encode("utf-8"), date_stamp.encode("utf-8"), hashlib.sha256).digest()
    k_region = hmac.new(k_date, region_name.encode("utf-8"), hashlib.sha256).digest()
    k_service = hmac.new(k_region, service_name.encode("utf-8"), hashlib.sha256).digest()
    k_signing = hmac.new(k_service, "aws4_request".encode("utf-8"), hashlib.sha256).digest()
    return hmac.new(k_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

async def handler(event, env):
    AWS_ACCESS_KEY = env.AWS_ACCESS_KEY
    AWS_SECRET_KEY = env.AWS_SECRET_KEY
    if not AWS_ACCESS_KEY or not AWS_SECRET_KEY:
        return "AWS credentials not found."

    # AWS request parameters
    action = event.request.query.get("action", "start")  # Start or stop instance
    service = "ec2"
    host = f"ec2.{REGION}.amazonaws.com"
    endpoint = f"https://{host}"
    method = "POST"
    content_type = "application/x-www-form-urlencoded; charset=utf-8"
    amz_target = "ec2.amazonaws.com"
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    date_stamp = datetime.datetime.utcnow().strftime("%Y%m%d")

    # Form body for EC2 action
    body = f"Action={action.capitalize()}Instances&InstanceId.1={INSTANCE_ID}&Version=2016-11-15"

    # Generate canonical request
    canonical_uri = "/"
    canonical_querystring = ""
    canonical_headers = f"host:{host}\n"
    signed_headers = "host"
    payload_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
    canonical_request = f"{method}\n{canonical_uri}\n{canonical_querystring}\n{canonical_headers}\n{signed_headers}\n{payload_hash}"

    # Generate string to sign
    algorithm = "AWS4-HMAC-SHA256"
    credential_scope = f"{date_stamp}/{REGION}/{service}/aws4_request"
    string_to_sign = f"{algorithm}\n{timestamp}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"

    # Generate signature
    signature = generate_aws_signature(AWS_SECRET_KEY, date_stamp, REGION, service, string_to_sign)

    # Generate authorization header
    authorization_header = (
        f"{algorithm} Credential={AWS_ACCESS_KEY}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )

    # Make the HTTP request
    headers = {
        "Content-Type": content_type,
        "X-Amz-Date": timestamp,
        "Authorization": authorization_header,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(endpoint, data=body, headers=headers)

    if response.status_code == 200:
        return f"EC2 instance {INSTANCE_ID} {action}ed successfully."
    else:
        return f"Error {response.status_code}: {response.text}"

