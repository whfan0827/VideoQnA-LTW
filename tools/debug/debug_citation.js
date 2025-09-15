// Debug citation issues - run this in browser console when citation fails

console.log("=== Citation Debug Tool ===");

// 1. Check if we have response data
function debugCitationData() {
    // Find all citation elements
    const citations = document.querySelectorAll('sup[data-docid]');
    console.log(`\nFound ${citations.length} citations:`);
    
    citations.forEach((citation, index) => {
        const docId = citation.dataset.docid;
        const path = citation.dataset.path;
        console.log(`\nCitation ${index + 1}:`);
        console.log(`  - docId: ${docId}`);
        console.log(`  - path: ${path}`);
        console.log(`  - path valid: ${path && path.startsWith('http')}`);
    });
}

// 2. Check docs_by_id structure
function checkDocsById() {
    // Try to find response data in React components
    console.log("\nLooking for docs_by_id data in page...");
    
    // Check if we can access the answer data somehow
    const answerElements = document.querySelectorAll('[class*="answerContainer"]');
    console.log(`Found ${answerElements.length} answer containers`);
    
    // Try to trigger a citation click to see what happens
    const firstCitation = document.querySelector('sup[data-docid]');
    if (firstCitation) {
        console.log("\nFirst citation details:");
        console.log("  - docId:", firstCitation.dataset.docid);
        console.log("  - path:", firstCitation.dataset.path);
        console.log("  - element:", firstCitation);
        
        // Check if path is empty or invalid
        const path = firstCitation.dataset.path;
        if (!path || path === "") {
            console.error("❌ Citation path is empty!");
        } else if (!path.startsWith("http")) {
            console.error("❌ Citation path is not a valid URL:", path);
        } else {
            console.log("✅ Citation path looks valid");
        }
    }
}

// 3. Test citation URL structure
function testCitationUrl() {
    console.log("\n=== Citation URL Test ===");
    
    // Sample data based on what we see in logs
    const sampleDocId = "9afc4fb5-375d-4900-94fc-6c0272caf290";
    console.log(`Testing with docId: ${sampleDocId}`);
    
    // Check if this looks like a Video Indexer citation
    if (sampleDocId.match(/^[0-9a-f-]{36}$/)) {
        console.log("✅ DocId format looks like a UUID (Video Indexer style)");
    } else {
        console.log("❌ DocId format doesn't match expected UUID pattern");
    }
}

// 4. Monitor iframe loading
function monitorIframe() {
    console.log("\n=== Iframe Monitoring ===");
    
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.type === 'childList') {
                const iframes = mutation.target.querySelectorAll?.('iframe[title="Citation"]') || [];
                iframes.forEach((iframe) => {
                    console.log("New iframe detected:");
                    console.log("  - src:", iframe.src);
                    console.log("  - ready state:", iframe.readyState);
                    
                    iframe.onload = () => console.log("✅ Iframe loaded successfully");
                    iframe.onerror = (e) => console.error("❌ Iframe failed to load:", e);
                });
            }
        });
    });
    
    observer.observe(document.body, { childList: true, subtree: true });
    console.log("Started monitoring for new iframes...");
}

// Run all debug functions
debugCitationData();
checkDocsById();
testCitationUrl();
monitorIframe();

console.log("\n✅ Citation debugging started. Click on a citation to see detailed logs.");