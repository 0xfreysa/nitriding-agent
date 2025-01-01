import fs from "fs";

console.log("Start generation of NFT collection");

fs.writeFile("./out/ahi.txt", new Date().toISOString(), (err: any) => {
  if (err) throw err;
});

console.log("NFT collection generation completed");
