// Function to load and parse CSV data
async function loadBlogPosts() {
    try {
        const response = await fetch('/data/blog_posts.csv');
        const csvText = await response.text();
        
        Papa.parse(csvText, {
            header: true,
            complete: function(results) {
                if (results.data && results.data.length > 0) {
                    renderBlogPosts(results.data);
                } else {
                    console.error('No data found in CSV file');
                }
            },
            error: function(error) {
                console.error('Error parsing CSV:', error);
            }
        });
    } catch (error) {
        console.error('Error loading CSV file:', error);
    }
} 