import React from "react";
import ReactDOM from "react-dom/client";
import { HashRouter, Routes, Route } from "react-router-dom";

import "./index.css";
import { setupFluentIcons } from "./icons";

import Layout from "./pages/layout/Layout";
import NoPage from "./pages/NoPage";
import OneShot from "./pages/oneshot/OneShot";

// Initialize Fluent UI icons with local fonts
setupFluentIcons();

export default function App() {
    return (
        <HashRouter>
            <Routes>
                <Route path="/" element={<Layout />}>                    
                    <Route index element={<OneShot />} />
                    <Route path="*" element={<NoPage />} />
                </Route>
            </Routes>
        </HashRouter>
    );
}

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
    <React.StrictMode>
        <App />
    </React.StrictMode>
);
