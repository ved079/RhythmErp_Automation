// This script creates HSN SAC entries via the Angular app's form
// We'll drive it from bash using agent-browser eval calls

const entries = [
  { number: "0101", type: "Commodity", desc: "Live horses, asses, mules and hinnies" },
  { number: "0201", type: "Commodity", desc: "Meat of bovine animals, fresh or chilled" },
  { number: "0301", type: "Commodity", desc: "Live fish" },
  { number: "0401", type: "Commodity", desc: "Milk and cream, not concentrated nor sweetened" },
  { number: "0501", type: "Commodity", desc: "Human hair, unworked, whether or not washed" },
  { number: "0601", type: "Commodity", desc: "Bulbs, tubers, corms and rhizomes, dormant" },
  { number: "0701", type: "Commodity", desc: "Potatoes, fresh or chilled" },
  { number: "0801", type: "Commodity", desc: "Coconuts, Brazil nuts and cashew nuts, fresh" },
  { number: "0901", type: "Commodity", desc: "Coffee, whether or not roasted or decaffeinated" },
  { number: "1001", type: "Commodity", desc: "Wheat and meslin" },
  { number: "995411", type: "Services", desc: "General construction services of buildings" },
  { number: "995412", type: "Services", desc: "Construction services of industrial buildings" },
  { number: "995413", type: "Services", desc: "Installation services of prefabricated structures" },
  { number: "995414", type: "Services", desc: "Building completion and finishing services" },
  { number: "995415", type: "Services", desc: "Building installation services" },
  { number: "996311", type: "Services", desc: "Food and beverage serving services with waiter" },
  { number: "996312", type: "Services", desc: "Catering services for events and functions" },
  { number: "997111", type: "Commission", desc: "Commission on sale of agricultural products" },
  { number: "997112", type: "Commission", desc: "Commission on purchase of raw materials" },
  { number: "996211", type: "Transportation", desc: "Road transport services for goods" }
];

console.log(JSON.stringify(entries));
