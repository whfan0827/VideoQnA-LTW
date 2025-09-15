// Run this in browser console to debug localStorage issues

console.log("=== Debugging localStorage and targetLibrary ===");

// 1. Show all localStorage contents
console.log("\n1. Current localStorage:");
for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    const value = localStorage.getItem(key);
    console.log(`  ${key}: ${value}`);
}

// 2. Check target_library specifically
const targetLibrary = localStorage.getItem('target_library');
console.log(`\n2. target_library value: "${targetLibrary}"`);

// 3. Check if it matches what you expect
console.log("\n3. Available libraries check:");
fetch('/indexes')
    .then(response => response.json())
    .then(indexes => {
        console.log("Available indexes:", indexes);
        
        if (targetLibrary) {
            const isValid = indexes.includes(targetLibrary);
            console.log(`target_library "${targetLibrary}" is valid: ${isValid}`);
            
            if (!isValid) {
                console.warn("❌ target_library is set to an invalid index!");
                console.log("Clearing invalid target_library...");
                localStorage.removeItem('target_library');
            }
        }
    })
    .catch(error => console.error("Error fetching indexes:", error));

// 4. Clear function
window.clearTargetLibrary = function() {
    console.log("Clearing target_library...");
    localStorage.removeItem('target_library');
    console.log("Done. Refresh the page.");
};

console.log("\nDebugging setup complete!");
console.log("Run clearTargetLibrary() to clear the target library setting.");
