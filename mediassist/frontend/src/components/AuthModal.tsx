import React, { useState } from "react";
import { Eye, EyeOff, Lock, Mail, User as UserIcon, X, Sparkles } from "lucide-react";

interface AuthModalProps {
    isOpen: boolean;
    onClose: () => void;
    onLogin: (email: string, pass: string) => Promise<void>;
    onRegister: (name: string, email: string, pass: string) => Promise<void>;
    loading: boolean;
    error: string;
}

export const AuthModal: React.FC<AuthModalProps> = ({
    isOpen,
    onClose,
    onLogin,
    onRegister,
    loading,
    error,
}) => {
    const [isRegister, setIsRegister] = useState(false);
    const [fullName, setFullName] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);

    if (!isOpen) return null;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (isRegister) {
            await onRegister(fullName, email, password);
        } else {
            await onLogin(email, password);
        }
    };

    const handleDemoFill = () => {
        setIsRegister(false);
        setEmail("user@test.com");
        setPassword("Pass123456789!");
    };

    return (
        <div className="auth-overlay" onClick={onClose} role="dialog" aria-modal="true">
            <div className="auth-modal-card" onClick={(e) => e.stopPropagation()}>
                <button
                    type="button"
                    className="modal-close-btn"
                    onClick={onClose}
                    aria-label="Close"
                >
                    <X size={20} />
                </button>

                <div className="auth-header">
                    <div className="auth-logo-badge">
                        <span className="heartbeat-dot"></span>
                        <span className="cross-symbol">✚</span>
                    </div>
                    <h2>{isRegister ? "Create MediAssist Account" : "Welcome Back to MediAssist"}</h2>
                    <p className="auth-subtitle">
                        {isRegister
                            ? "Get personal health intelligence, prescription OCR, and record tracking."
                            : "Log in to access your secure consultations and health profile."}
                    </p>
                </div>

                <div className="auth-tabs">
                    <button
                        type="button"
                        className={`auth-tab ${!isRegister ? "active" : ""}`}
                        onClick={() => setIsRegister(false)}
                    >
                        Sign In
                    </button>
                    <button
                        type="button"
                        className={`auth-tab ${isRegister ? "active" : ""}`}
                        onClick={() => setIsRegister(true)}
                    >
                        Register
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="auth-form">
                    {isRegister && (
                        <div className="input-group">
                            <label htmlFor="reg-name">Full Name</label>
                            <div className="input-field-wrapper">
                                <UserIcon size={18} className="field-icon" />
                                <input
                                    id="reg-name"
                                    type="text"
                                    placeholder="Dr. Jane Smith or John Doe"
                                    value={fullName}
                                    onChange={(e) => setFullName(e.target.value)}
                                    required
                                    disabled={loading}
                                />
                            </div>
                        </div>
                    )}

                    <div className="input-group">
                        <label htmlFor="auth-email">Email Address</label>
                        <div className="input-field-wrapper">
                            <Mail size={18} className="field-icon" />
                            <input
                                id="auth-email"
                                type="email"
                                placeholder="name@example.com"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                                disabled={loading}
                            />
                        </div>
                    </div>

                    <div className="input-group">
                        <label htmlFor="auth-password">
                            Password {isRegister && <span className="helper-label">(min. 12 characters)</span>}
                        </label>
                        <div className="input-field-wrapper">
                            <Lock size={18} className="field-icon" />
                            <input
                                id="auth-password"
                                type={showPassword ? "text" : "password"}
                                placeholder="••••••••••••"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                minLength={isRegister ? 12 : 1}
                                required
                                disabled={loading}
                            />
                            <button
                                type="button"
                                className="visibility-btn"
                                onClick={() => setShowPassword(!showPassword)}
                                title={showPassword ? "Hide password" : "Show password"}
                                tabIndex={-1}
                            >
                                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                            </button>
                        </div>
                    </div>

                    {error && (
                        <div className="alert-box alert-error">
                            <span>{error}</span>
                        </div>
                    )}

                    <button
                        type="submit"
                        className="btn btn-primary btn-block btn-lg"
                        disabled={loading}
                    >
                        {loading
                            ? "Authenticating..."
                            : isRegister
                            ? "Create Free Account"
                            : "Sign In"}
                    </button>
                </form>

                <div className="auth-footer">
                    <button
                        type="button"
                        className="btn btn-secondary btn-sm mb-3"
                        onClick={handleDemoFill}
                    >
                        <Sparkles size={14} className="text-emerald-500" />
                        <span>Quick Fill Test Account</span>
                    </button>
                    <p>
                        {isRegister ? "Already registered?" : "Don't have an account yet?"}{" "}
                        <button
                            type="button"
                            className="link-btn"
                            onClick={() => setIsRegister(!isRegister)}
                        >
                            {isRegister ? "Sign In here" : "Sign Up free"}
                        </button>
                    </p>
                </div>
            </div>
        </div>
    );
};
