// bot/index.js
require('dotenv').config();
const { Client, GatewayIntentBits } = require('discord.js');
const fetch = (...args) => import('node-fetch').then(({default: fetch}) => fetch(...args));

const client = new Client({ 
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent,
    ] 
});

const API_URL = 'http://localhost:8000/api/chat';

client.on('ready', () => {
    console.log(`Logged in as ${client.user.tag}!`);
});

client.on('messageCreate', async (message) => {
    // Don't respond to bots or messages without mentions
    if (message.author.bot) return;
    if (!message.mentions.has(client.user.id)) return;

    const prompt = message.content.replace(`<@${client.user.id}>`, '').trim();
    if (!prompt) return;

    try {
        // Send initial "typing" indicator
        await message.channel.sendTyping();
        const reply = await message.reply('Thinking...');
        
        const apiUrl = API_URL;
        console.log('Sending request to:', apiUrl);
        
        let responseText = ''; // Moved to top of try block for better scoping
        
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'text/event-stream'
            },
            body: JSON.stringify({
                content: prompt
            })
        });

        console.log('Response status:', response.status);

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API request failed: ${response.status} ${response.statusText}\n${errorText}`);
        }

        // Ensure we have a readable stream
        if (!response.body) {
            throw new Error('Response body is not a readable stream');
        }
        
        // Use node-fetch's built-in streaming
        response.body.on('data', async (chunk) => {
            const text = chunk.toString();
            const lines = text.split('\n').filter(line => line.trim() !== '');
            
            for (const line of lines) {
                try {
                    const trimmedLine = line.trim();
                    if (!trimmedLine || trimmedLine === 'data: [DONE]') continue;
                    
                    const jsonStr = trimmedLine.startsWith('data: ') ? 
                        trimmedLine.slice(6).trim() : trimmedLine;
                    
                    const data = JSON.parse(jsonStr);
                    if (data.response) {
                        responseText += data.response;
                        // Update the message with the latest response
                        if (responseText.trim()) {
                            await reply.edit(responseText);
                        }
                    }
                } catch (e) {
                    console.error('Error processing line:', line);
                    console.error('Error details:', e);
                }
            }
        });
        
        // Handle stream end
        response.body.on('end', () => {
            console.log('Stream ended');
        });
        
        // Handle errors
        response.body.on('error', (error) => {
            console.error('Stream error:', error);
            reply.edit('Sorry, there was an error processing your request.');
        });
        
        // Response handling is now done via event listeners
        // responseText is already declared at the top of the try block
    } catch (error) {
        console.error('Error:', error);
        try {
            await message.reply(`Sorry, I encountered an error: ${error.message}`);
        } catch (e) {
            console.error('Failed to send error message:', e);
        }
    }
});

// Start the bot
client.login(process.env.DISCORD_BOT_TOKEN);