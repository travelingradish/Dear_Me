# Dear Me Frontend 💝

The React TypeScript frontend for Dear Me - a gentle, AI-powered journaling companion.

## 🏗️ Tech Stack

- **React 19.1.1** with TypeScript
- **Tailwind CSS** for styling
- **React Context** for state management
- **Axios** for API communication
- **React Testing Library** for testing

## 🚀 Quick Start

### Prerequisites
- **Node.js 16+**
- **npm** or **yarn**

### Installation & Development

```bash
# Install dependencies
npm install

# Start development server
npm start
```

The frontend will run on **http://localhost:3000**

⚠️ **Important**: The backend must be running on http://localhost:8001 for the frontend to work properly.

## 🧪 Testing

```bash
# Run all tests
npm test

# Run tests with coverage
npm test -- --coverage

# Run specific component tests
npm test -- --testNamePattern="Home"
```

## 🏭 Production Build

```bash
# Create production build
npm run build

# The build folder will contain the optimized production files
```

## 📁 Project Structure

```
src/
├── components/           # React components
│   ├── Home.tsx         # Landing page with mode selection
│   ├── GuidedChat.tsx   # AI-guided conversations
│   ├── SimpleChat.tsx   # Casual chat mode
│   ├── FreeEntry.tsx    # Free writing mode
│   ├── SimpleCalendar.tsx # Unified calendar
│   └── Login.tsx        # Authentication
├── contexts/
│   └── AuthContext.tsx  # Authentication state
├── utils/
│   └── api.ts          # API client
├── types/              # TypeScript definitions
└── App.tsx            # Main application
```

## 🎨 Key Features

- **Three Journaling Modes**: Guided, Casual, and Free Entry
- **Unified Calendar**: View entries from all modes in one place
- **Real-time AI Chat**: Instant responses and conversation flow
- **Responsive Design**: Works across different screen sizes
- **Authentication**: Secure login and registration
- **AI Character Naming**: Personalized AI companion experience

## 🤝 Contributing

1. Follow the existing code style and patterns
2. Use TypeScript for all new components
3. Write tests for new functionality
4. Ensure responsive design principles

## 📚 Learn More

- [React Documentation](https://reactjs.org/)
- [TypeScript Documentation](https://www.typescriptlang.org/)
- [Tailwind CSS Documentation](https://tailwindcss.com/)

---

Part of the **Dear Me v1.0** journaling application.