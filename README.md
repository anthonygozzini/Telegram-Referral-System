
# Telegram Referral System Bot

This repository contains a Python-based Telegram bot that manages a referral system. The bot rewards users with points for referring others to join a Telegram channel and group. Users can also link their wallet addresses to their account, and the bot tracks their progress and referral status.

## Features

- **User Registration**: Automatically registers users when they start the bot.
- **Referral System**: Users can refer others using a unique referral link.
- **Wallet Address Submission**: Users can submit their wallet addresses, which are stored securely.
- **Membership Verification**: Ensures that users have joined the required Telegram channel and group before they can proceed.
- **Points System**: Users earn points for referring others and completing required steps.
- **Admin Functionality**: Admins can view the top 10 users based on points.

## Setup Instructions

1. **Clone the Repository**:
    ```
    git clone https://github.com/anthonygozzini/Telegram-Referral-System.git
    cd Telegram-Referral-System
    ```

2. **Install Dependencies**:
    The bot requires Python 3.6 or higher. Install the necessary Python packages using pip:
    ```
    pip install -r requirements.txt
    ```

3. **Environment Variables**:
    Create a `.env` file in the root directory and populate it with your Telegram bot token, channel ID, group ID, and other required details:
    ```
    TELEGRAM_TOKEN=your_telegram_bot_token
    CHANNEL_ID=your_channel_id
    GROUP_ID=your_group_id
    CHANNEL_URL=your_channel_url
    GROUP_URL=your_group_url
    SOCIAL_LINK_1=your_social_link_1
    SOCIAL_LINK_2=your_social_link_2
    ADMINS=your_admin_user_ids_comma_separated
    DATABASE_PATH=bot_data.db
    ```

4. **Run the Bot**:
    Execute the following command to start the bot:
    ```
    python Telegram-Referral-System.py
    ```

## Bot Commands

- **/start**: Registers the user and provides the main menu with options.
- **/admin**: Shows the top 10 users based on points (Admin only).

## Code Structure

- **Telegram-Referral-System.py**: Main script that initializes the bot, defines handlers, and manages the referral system logic.
- **.env**: Environment variables configuration file.
- **requirements.txt**: Lists the Python dependencies for the project.

## License

This project is open-source and available under the MIT License.
