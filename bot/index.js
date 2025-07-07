require('dotenv').config();
const { Client, GatewayIntentBits } = require('discord.js');
const fetch = require('node-fetch').default;  // Updated this line

const client = new Client({ 
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent,
    ] 
});

// API configuration
const API_URL = "http://localhost:8000/api/chat";

client.once('ready', () => {
    console.log(`🤖 Logged in as ${client.user.tag}!`);
});

client.on('messageCreate', async (message) => {
    // Don't respond to bots or messages without mentions
    if (message.author.bot) return;
    if (!message.mentions.has(client.user.id)) return;
    
    const prompt = message.content.replace(`<@${client.user.id}>`, '').trim();
    if (!prompt) return;
    
    try {
        // Show typing indicator
        await message.channel.sendTyping();
        
        console.log('Sending request to API...');
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                messages: [
                    { role: 'system', content: 'You are a helpful assistant.' },
                    { role: 'user', content: prompt }
                ]
            })
        });

        console.log('Response status:', response.status);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('API Error:', errorText);
            throw new Error(`API request failed: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        console.log('API Response:', JSON.stringify(data, null, 2));
        
        // Clean up and send the response back to Discord
        if (data.response) {
            // Clean up the response
            let cleanResponse = data.response
                .replace(/^<\|assistant\|>\s*/, '')  // Remove <|assistant|> from start
                .replace(/<\|[^>]+\|>/g, '')         // Remove any other <|...|> tags
                .trim();
            
            // Split message if it's too long for Discord
            if (cleanResponse.length > 2000) {
                const chunks = cleanResponse.match(/[\s\S]{1,1900}[\n.?!]|[\s\S]{1,2000}/g) || [cleanResponse];
                for (const chunk of chunks) {
                    if (chunk.trim()) {  // Only send non-empty chunks
                        await message.reply(chunk);
                        // Add a small delay to avoid rate limiting
                        await new Promise(resolve => setTimeout(resolve, 1000));
                    }
                }
            } else if (cleanResponse.trim()) {  // Only send non-empty responses
                await message.reply(cleanResponse);
            } else {
                await message.reply("I'm here! How can I assist you?");
            }
        } else {
            throw new Error('No response from model');
        }
    } catch (error) {
        console.error('Error:', error);
        await message.reply(`Sorry, I encountered an error: ${error.message}`);
    }
});

// Login to Discord
client.login(process.env.DISCORD_TOKEN)
    .then(() => console.log('Bot is connecting to Discord...'))
    .catch(console.error);