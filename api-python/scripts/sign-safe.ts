import { sepolia } from "viem/chains";
//import { EthersAdapter } from "@safe-global/protocol-kit";
import SafeApiKit from "@safe-global/api-kit";
import Safe from "@safe-global/protocol-kit";
import { MetaTransactionData, OperationType } from "@safe-global/types-kit";
import { ethers } from "ethers";

const RPC_URL =
  "https://base-mainnet.g.alchemy.com/v2/DChWancKklfohbd3LKBDcRuIqbpZsGk0";

// const {
//   default: Safe,
//   SigningMethod,
//   // buildContractSignature,
//   hashSafeMessage,
//   buildSignatureBytes,
// } = pkg;
// const { default: SafeApiKit } = apiKitPkg;

const SEPIOLA = sepolia.rpcUrls.default.http[0];

// async function signWithSafe(safeAddress, ownerKey, message) {
//   try {
//     console.error("\n=== Starting Safe signing process ===");
//     console.error("Safe Address:", safeAddress);
//     console.error("Owner Key:", ownerKey.slice(0, 10) + "...");

//     // Initialize Protocol Kit
//     console.error("\n1. Initializing Protocol Kit...");
//     const protocolKit = await Safe.init({
//       provider: SEPIOLA,
//       safeAddress: safeAddress,
//       signer: ownerKey,
//     });
//     console.error("Protocol Kit initialized");

//     // Initialize API Kit
//     console.error("\n2. Initializing API Kit...");
//     const apiKit = new SafeApiKit({ chainId: 11155111 });
//     console.error("API Kit initialized");

//     // Create and sign message
//     console.error("\n3. Creating and signing message...");
//     let safeMessage = protocolKit.createMessage(message);
//     safeMessage = await protocolKit.signMessage(
//       safeMessage,
//       SigningMethod.SAFE_SIGNATURE
//     );
//     console.error("Message signed");
//     console.error("Current signature:", safeMessage.signatures);

//     // Get message hash
//     const safeMessageHash = await protocolKit.getSafeMessageHash(
//       hashSafeMessage(message)
//     );
//     console.error("Message hash:", safeMessageHash);

//     // Submit to API
//     console.error("\n4. Submitting to Safe Transaction Service...");
//     const ownerSignature = Array.from(safeMessage.signatures.values())[0];
//     await apiKit.addMessage(safeAddress, {
//       message: message,
//       signature: buildSignatureBytes([ownerSignature]),
//     });
//     console.error("Message submitted");

//     return {
//       success: true,
//       message: safeMessage.data,
//       signature: ownerSignature.data,
//       signer: await protocolKit.getAddress(),
//       messageHash: safeMessageHash,
//     };
//   } catch (error) {
//     console.error("\n!!! Error in signWithSafe !!!");
//     console.error("Error occurred:", error.message);
//     console.error("Stack trace:", error.stack);
//     return {
//       success: false,
//       error: error.message,
//     };
//   }
// }

async function signWithSafe2(safeAddress: string, ownerKey: string) {
  // Derive public key from owner key
  const wallet = new ethers.Wallet(ownerKey);
  const publicKey = wallet.address;

  const apiKit = new SafeApiKit({
    chainId: BigInt(8453)
  });

  const protocolKitOwner1 = await Safe.init({
    provider: RPC_URL,
    signer: ownerKey,
    safeAddress: safeAddress
  });

  const safeTransactionData = {
    to: "0x86693CbE3f2581DF512635823F46f0d593D96dbA",
    value: "2", // 1 wei
    data: "0x",
    operation: OperationType.Call
  };

  const safeTransaction = await protocolKitOwner1.createTransaction({
    transactions: [safeTransactionData]
  });

  const safeTxHash = await protocolKitOwner1.getTransactionHash(
    safeTransaction
  );
  const signature = await protocolKitOwner1.signHash(safeTxHash);

  await apiKit.proposeTransaction({
    safeAddress: safeAddress,
    safeTransactionData: safeTransaction.data,
    safeTxHash,
    senderAddress: publicKey,
    senderSignature: signature.data
  });
}

async function main() {
  const privkey = process.argv[2];
  const safeAddress = process.argv[3];
  //const safeAddress = "0x6Bb1D5DeAd873066F1174f6Fc6fE213047408442";

  if (!safeAddress) {
    console.error("Please provide a safe address as the first argument");
    process.exit(1);
  }

  if (!privkey) {
    console.error("Please provide a private key as the second argument");
    process.exit(1);
  }

  console.log(privkey);

  await signWithSafe2(safeAddress, privkey);
  console.log("Tx signed");
}

main();
