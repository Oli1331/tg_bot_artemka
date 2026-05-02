# 🤖 Telegram Assistant Bot

A multifunctional Telegram bot that provides:
- 🌤 Weather updates  
- 📅 University schedule (via ICS parsing)  
- 🎲 Random advice about skipping lessons  
- 👤 User info  

Built with Python using Telegram Bot API.

---

## 🚀 Features

### 🌤 Weather
- Shows current weather  
- Supports quick refresh via button  
- Uses Rambler Weather API  

---

### 📅 Schedule
- Fetches schedule from university website (ICS format)  
- Parses recurring events  
- Shows today's lessons:
  - time  
  - subject  
  - teacher  
  - location  

---

### 🎲 Skip Lesson
- Randomly decides whether you should skip a class  
- Adds fun responses  

---

### 👤 User Info
- Displays user data from Telegram  

---

### 💾 Database
- Stores users in SQLite database  
- Prevents duplicates  

---

## 🧠 Technologies

- Python 3  
- telebot (pyTelegramBotAPI)  
- requests  
- sqlite3  
- icalendar  
- dateutil  
