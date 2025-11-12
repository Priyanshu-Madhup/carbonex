# EcoSphere AI - Eco-Themed Landing Page

A visually stunning, eco-themed landing page for EcoSphere AI platform with functional authentication system. Built with React and FastAPI.

## Features

- 🌿 Beautiful eco-friendly design with smooth animations
- 🔐 Functional login and signup system
- 💾 SQLite-based authentication
- 🎨 Glassmorphism effects and gradient designs
- 📱 Fully responsive layout
- ⚡ Real-time session management

## Tech Stack

**Frontend:**
- React 18
- CSS3 with animations
- LocalStorage for session persistence

**Backend:**
- FastAPI
- SQLite
- SHA-256 password hashing

## Getting Started

### Prerequisites

- Node.js (v14 or higher)
- Python 3.8 or higher
- npm or yarn

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/Priyanshu-Madhup/carbonex.git
cd carbonex
```

2. **Install frontend dependencies:**
```bash
npm install
```

3. **Install backend dependencies:**
```bash
cd backend
pip install -r requirements.txt
cd ..
```

### Running the Application

You need to run both the backend and frontend servers:

**Terminal 1 - Start the Backend:**
```bash
cd backend
python main.py
```
Backend will run on `http://localhost:8000`

**Terminal 2 - Start the Frontend:**
```bash
npm start
```
Frontend will run on `http://localhost:3000`

The browser should automatically open to `http://localhost:3000`

## Usage

1. Click the **Signup** button in the navbar to create a new account
2. Fill in your name, email, and password
3. After successful signup, you'll be automatically logged in
4. Use the **Login** button to sign in with existing credentials
5. Click **Logout** to end your session

## API Endpoints

- `POST /api/signup` - Register a new user
- `POST /api/login` - Login with credentials
- `GET /api/verify` - Verify authentication token
- `POST /api/logout` - Logout and clear session

## Project Structure

```
carbonex/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── requirements.txt     # Python dependencies
│   └── README.md           # Backend documentation
├── src/
│   ├── components/
│   │   ├── Login.js        # Login component
│   │   ├── Signup.js       # Signup component
│   │   └── Auth.css        # Auth styling
│   ├── App.js              # Main React component
│   ├── App.css             # Main styling
│   └── index.js            # React entry point
└── package.json            # Frontend dependencies
```

## Security Notes

This is a basic authentication system for demonstration purposes. For production deployment:
- Use bcrypt or Argon2 for password hashing
- Implement rate limiting
- Add HTTPS/SSL
- Use environment variables for configuration
- Implement CSRF protection
- Add email verification
- Use JWT tokens with proper expiration

## Contributing

Feel free to submit issues and pull requests!

## License

This project is open source and available under the MIT License.

---

## Available Scripts

### `npm start`

Runs the app in the development mode.\
Open [http://localhost:3000](http://localhost:3000) to view it in your browser.

The page will reload when you make changes.\
You may also see any lint errors in the console.

### `npm test`

Launches the test runner in the interactive watch mode.\
See the section about [running tests](https://facebook.github.io/create-react-app/docs/running-tests) for more information.

### `npm run build`

Builds the app for production to the `build` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.

The build is minified and the filenames include the hashes.\
Your app is ready to be deployed!

See the section about [deployment](https://facebook.github.io/create-react-app/docs/deployment) for more information.

### `npm run eject`

**Note: this is a one-way operation. Once you `eject`, you can't go back!**

If you aren't satisfied with the build tool and configuration choices, you can `eject` at any time. This command will remove the single build dependency from your project.

Instead, it will copy all the configuration files and the transitive dependencies (webpack, Babel, ESLint, etc) right into your project so you have full control over them. All of the commands except `eject` will still work, but they will point to the copied scripts so you can tweak them. At this point you're on your own.

You don't have to ever use `eject`. The curated feature set is suitable for small and middle deployments, and you shouldn't feel obligated to use this feature. However we understand that this tool wouldn't be useful if you couldn't customize it when you are ready for it.

## Learn More

You can learn more in the [Create React App documentation](https://facebook.github.io/create-react-app/docs/getting-started).

To learn React, check out the [React documentation](https://reactjs.org/).

### Code Splitting

This section has moved here: [https://facebook.github.io/create-react-app/docs/code-splitting](https://facebook.github.io/create-react-app/docs/code-splitting)

### Analyzing the Bundle Size

This section has moved here: [https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size](https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size)

### Making a Progressive Web App

This section has moved here: [https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app](https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app)

### Advanced Configuration

This section has moved here: [https://facebook.github.io/create-react-app/docs/advanced-configuration](https://facebook.github.io/create-react-app/docs/advanced-configuration)

### Deployment

This section has moved here: [https://facebook.github.io/create-react-app/docs/deployment](https://facebook.github.io/create-react-app/docs/deployment)

### `npm run build` fails to minify

This section has moved here: [https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify](https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify)
