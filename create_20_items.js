// 20 unique, natural commodity attribute names with descriptions and UOMs
const items = [
  { name: "Rice", uom: "MT", desc: "Rice paddy commodity" },
  { name: "Cotton", uom: "QT", desc: "Raw cotton bales" },
  { name: "Sugarcane", uom: "MT", desc: "Sugarcane crop yield" },
  { name: "Tur Dal", uom: "QT", desc: "Pigeon pea pulses" },
  { name: "Groundnut", uom: "KG", desc: "Groundnut kernels" },
  { name: "Soybean", uom: "MT", desc: "Soybean oilseed crop" },
  { name: "Maize", uom: "MT", desc: "Maize corn grain" },
  { name: "Jowar", uom: "QT", desc: "Sorghum millet grain" },
  { name: "Bajra", uom: "QT", desc: "Pearl millet grain" },
  { name: "Ragi", uom: "KG", desc: "Finger millet grain" },
  { name: "Onion", uom: "QT", desc: "Fresh onion bulbs" },
  { name: "Potato", uom: "QT", desc: "Fresh potato tubers" },
  { name: "Tomato", uom: "KG", desc: "Fresh tomato produce" },
  { name: "Chilli", uom: "KG", desc: "Dry red chilli" },
  { name: "Turmeric", uom: "KG", desc: "Turmeric finger dry" },
  { name: "Ginger", uom: "KG", desc: "Fresh ginger root" },
  { name: "Garlic", uom: "KG", desc: "Dry garlic bulbs" },
  { name: "Coriander", uom: "KG", desc: "Coriander seeds dry" },
  { name: "Cumin", uom: "KG", desc: "Cumin seeds dry" },
  { name: "Mustard", uom: "KG", desc: "Mustard oilseeds" }
];

async function createOne(page, item) {
  // This script will be called from bash loop
  console.log(JSON.stringify(item));
}

// Just output the items array for the bash script to consume
console.log(JSON.stringify(items));
