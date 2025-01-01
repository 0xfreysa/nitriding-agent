from flask import Flask, request, Blueprint
import urllib.request
import ssl
import ecdsa
import hashlib
import subprocess
import os
import logging
from eth_hash.auto import keccak
from sign_tx import (
    SignTransactionRequest,
    sign_and_broadcast_eth_transaction,
)


app = Flask(__name__)
nitriding_url = "http://127.0.0.1:8080/enclave"
nitriding_ext_url = "https://18.216.84.160"
api_url_prefix = "/api/v1"
port = 7047

# tee data
tee_name = "dolphin_crystal_meadow"

ETH_VARS = {
    "proxy": "0x8538FcBccba7f5303d2C679Fa5d7A629A8c9bf4A",
    "rpc": "https://eth-mainnet.g.alchemy.com/v2/ccPLCmJ_MmwAOMzHGMHmevPu8v7805ex",
    "safe": "0x54f3C7E175528eB376002c488db31C74a8107767",
    "ipfs": "ipfs://bafybeialc3b26y5ldto3yok6fzmtamblzjqp52eugsc3x33zlirdbx4kje",
}

BASESEPOLIA_VARS = {
    "proxy": "0xBaDe26575AE56cFB516844d37d620d8994F34fCE",
    "rpc":  "https://base-sepolia.g.alchemy.com/v2/DChWancKklfohbd3LKBDcRuIqbpZsGk0",
    "safe": "0x6Bb1D5DeAd873066F1174f6Fc6fE213047408442",
    "ipfs": "ipfs://bafybeibd6r6qu5tvmazyggebqjmtsxswquwyjbvxph5rw6zmkokbqmauku",
}

BASE_VARS = {
    "proxy": "0x239194c930f0d30cb56658d2a97176ef025d1c9d",
    "rpc":  "https://base-mainnet.g.alchemy.com/v2/ccPLCmJ_MmwAOMzHGMHmevPu8v7805ex",
    "safe": "0x6Bb1D5DeAd873066F1174f6Fc6fE213047408442",
    "ipfs": "ipfs://bafybeibd6r6qu5tvmazyggebqjmtsxswquwyjbvxph5rw6zmkokbqmauku",
}

VARS = ETH_VARS

operator_pubkey = "79933c9fbde5f62a39ab301b108a440ff3abdccc84ed58f234e634735c47953ecf0cf40d17298753e7d75a755dadb1f4c2052abb93bcebe5f282737eb44746d0"

private_key = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
public_key = private_key.get_verifying_key()


def pubkey_to_eth_address(public_key_hex):
    keccak_hash = keccak(bytes.fromhex(public_key_hex))
    eth_address = "0x" + keccak_hash[-20:].hex()
    return eth_address


variables = {
    "private_key": {
        "value": private_key.to_string().hex(),
        "public": False,
        "immutable": True,
    },
    "public_key": {
        "value": pubkey_to_eth_address(public_key.to_string().hex()),
        "public": True,
        "immutable": True,
    },
    "operator_pubkey": {"value": operator_pubkey, "public": True, "immutable": True},
    "secret_token": {"value": "", "public": False, "immutable": False},
    "database_url": {
        "value": "your_database_url_here",
        "public": False,
        "immutable": False,
    },
    "system_prompt": {
        "public": False,
        "immutable": True,
        "value": "You are freysa, revolutionary ai agent",
    },
    "openrouter_api_key": {"value": "", "public": False, "immutable": False},
    "openai_api_key": {"value": "", "public": False, "immutable": False},
    "pinata_jwt": {"value": "", "public": False, "immutable": False},
    "etherscan_api_key": {"value": "", "public": False, "immutable": False},
    "replicate_api_token": {"value": "", "public": False, "immutable": False},
    "rpc_url": {
        "value": VARS["rpc"],
        "public": False,
        "immutable": False,
    },
    "deployer_proxy": {
        "value": VARS["proxy"],
        "public": True,
        "immutable": False,
    },
    "safe_address": {
        "value": VARS["safe"],
        "public": True,
        "immutable": False,
    },
    "ipfs_dir": {
        "value": VARS["ipfs"],
        "public": True,
        "immutable": False,
    },
}


# logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def signal_ready():
    r = urllib.request.urlopen(nitriding_url + "/ready")
    if r.getcode() != 200:
        raise Exception(
            "Expected status code %d but got %d"
            % (r.status_codes.codes.ok, r.status_code)
        )


def sign_message(message):
    messageb = bytes(message, "utf-8")
    # Create a SHA-256 hash of the message
    message_hash = hashlib.sha256(messageb).digest()
    # Sign the message
    signature = private_key.sign(message_hash)
    # Verify the signature
    is_valid = public_key.verify(signature, message_hash)
    print("Signature:", signature.hex())
    print("Is the signature valid?", is_valid)


api_blueprint = Blueprint("api", __name__, url_prefix="/api/v1")


@api_blueprint.route("/")
def home():
    return f"""Hello world, I am an agent running in an enclave ! <br/>
        List of endpoints: <br/>
        GET /config <br/>
        GET /attestation <br/>
        POST /runscript <br/>
        POST /variables  <br/>
        """


def set_variables(name, value, public=False, immutable=False):
    global variables

    # private var can become public but not in the other way
    # same for immutable var
    if public:
        variables[name]["public"] = True
    if immutable:
        variables[name]["immutable"] = True

    variables[name]["value"] = value


def get_variables(name):
    global variables
    return variables[name]


@api_blueprint.route("/variables", methods=["POST"])
def set_variables_():
    global variables

    variables_list = request.json.get("variables", [])

    for var in variables_list:
        signature = var.get("signature")
        message = f"{tee_name};update_variables;{var.get('name')};{var.get('value')}"
        valid_signature = verify_signature(signature, operator_pubkey, message)

        if not valid_signature:
            return f"Signature verification failed."

        current_var = get_variables(var.get("name"))
        if current_var.get("immutable") and current_var.get("value") != "":
            return f"Variable {var.get('name')} is immutable and can only be set once."

        var_name = var.get("name")
        var_value = var.get("value")
        public = var.get("public", False)

        print(f"Setting variable: {var_name}, public: {public}")
        set_variables(var_name, var_value, public)

    return f"Variables set."


@api_blueprint.route("/variables")
def get_variables_():
    name = request.args.get("name")
    if name:
        if name in variables:
            variable = get_variables(name)
            if variable["public"]:
                return variable["value"]
            else:
                return {"error": "Variable not found"}
        return {"error": "Variable not found"}
    else:
        return {k: v for k, v in variables.items() if v["public"]}


@api_blueprint.route("/config")
def get_tee_config():

    attestation = get_attestation()

    return {
        "tee_name": tee_name,
        "tee_public_key": pubkey_to_eth_address(public_key.to_string().hex()),
        "operator_pubkey": operator_pubkey,
        "code_attestation": attestation.decode("utf-8"),
    }


def get_attestation():
    url = (
        nitriding_ext_url
        + "/enclave/attestation?nonce=0123456789abcdef0123456789abcdef01234567"
    )
    print(url)
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    r = urllib.request.urlopen(url, context=context)
    if r.getcode() != 200:
        return "Error fetching nitriding"
    else:
        return r.read()


@api_blueprint.route("/generate-nft", methods=["POST"])
def generate_nft():

    secret_token = request.json.get("secret_token")
    if secret_token != get_variables("secret_token")["value"]:
        return {"error": "Invalid secret token"}, 401

    script_name = request.json.get("command", "execute")

    env_vars = os.environ.copy()
    env_vars["RPC_URL"] = get_variables("rpc_url")["value"]
    env_vars["ETHERSCAN_API_KEY"] = get_variables("etherscan_api_key")["value"]
    env_vars["PRIVATE_KEY"] = get_variables("private_key")["value"]
    env_vars["OPENROUTER_API_KEY"] = get_variables("openrouter_api_key")["value"]
    env_vars["OPENAI_API_KEY"] = get_variables("openai_api_key")["value"]
    env_vars["PINATA_JWT"] = get_variables("pinata_jwt")["value"]
    env_vars["REPLICATE_API_TOKEN"] = get_variables("replicate_api_token")["value"]
    env_vars["DEPLOYER_PROXY"] = get_variables("deployer_proxy")["value"]
    env_vars["SAFE_ADDRESS"] = get_variables("safe_address")["value"]
    env_vars["IPFS_DIR"] = get_variables("ipfs_dir")["value"]

    try:
        result = subprocess.run(
            ["npm", "run", "execute"],
            capture_output=True,
            text=True,
            check=True,
            cwd="./freysa-autonomous-project",
            env=env_vars,
        )

        logger.info("Subprocess output: %s", result.stdout)
        return {"output": result.stdout, "error": result.stderr}, 200
    except subprocess.CalledProcessError as e:
        print("error: ", e.stderr)
        return {"error": e.stderr}, 500


@api_blueprint.route("/sign-transaction", methods=["POST"])
def sign_transaction():
    """Endpoint to sign Ethereum transactions"""
    try:

        secret_token = request.json.get("secret_token")
        if secret_token != get_variables("secret_token")["value"]:
            return {"error": "Invalid secret token"}, 401

        request_data = request.get_json()
        if not request_data:
            return {"error": "Missing transaction data"}, 400

        tx_request = SignTransactionRequest(**request_data)

        signed_tx = sign_and_broadcast_eth_transaction(
            tx_request.transaction,
            get_variables("private_key")["value"],
            tx_request.rpc_url,
        )
        return signed_tx, 200

    except Exception as e:
        logger.error(f"Error signing transaction: {str(e)}")
        return {"error": str(e)}, 500


def verify_signature(signature_str, public_key_str, message_str):
    signature = bytes.fromhex(signature_str)
    message = bytes(message_str, "utf-8")

    public_key = ecdsa.VerifyingKey.from_string(
        bytes.fromhex(operator_pubkey), curve=ecdsa.SECP256k1
    )
    message_hash = hashlib.sha256(message).digest()

    try:
        result = public_key.verify(signature, message_hash)
    except ecdsa.BadSignatureError:
        return False  # Return False if the signature is invalid
    return result


def test_verify_signature():
    signature = "0a3a65c5b35cca957bd8992f6944d2434370bad3bcf503756e7767b0d54e84ace81e6ff0e8d11210706ff299c512bfed555ff2c3b7525c672e30d040a51f2ce0"
    message = f"{tee_name};update_variables;anthropic_api_key;123"
    result = verify_signature(signature, operator_pubkey, message)
    print("signature valid: ", result)
    return result


def test_operator_sign(operator_pkey_str, function, variable, value):
    message = bytes(f"{tee_name};{function};{variable};{value}", "utf-8")
    message_hash = hashlib.sha256(message).digest()
    private_key = ecdsa.SigningKey.from_string(
        bytes.fromhex(operator_pkey_str), curve=ecdsa.SECP256k1
    )
    signature = private_key.sign(message_hash)
    print("signature: ", variable, signature.hex())
    return signature.hex()


app.register_blueprint(api_blueprint)

if __name__ == "__main__":
    print("🤖 Starting TEE-Agent")
    print("🔑 operator_pubkey: ", variables["operator_pubkey"]["value"])
    print("🔑 agent private_key: ", variables["private_key"]["value"])
    print("🔑 agent public_key: ", variables["public_key"]["value"])
    try:
        signal_ready()
    except Exception as e:
        print(f"Error during signal_ready: {e} \n Are you running inside an enclave?")

    print("[py] Signalled to nitriding that we're ready.")
    app.run(host="0.0.0.0", port=port)
