import React, { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import {
    AlertTriangle,
    Camera,
    Check,
    Copy,
    Download,
    Eye,
    FileText,
    HeartPulse,
    Loader2,
    Menu,
    Mic,
    MicOff,
    Paperclip,
    PhoneCall,
    Send,
    Sparkles,
    Square,
    Stethoscope,
    Trash2,
    Upload,
    Volume2,
    VolumeX,
    X,
} from "lucide-react";
import type { Conversation, ExtractedDocument, Message, User } from "../types";
import { ImageLightbox } from "./ImageLightbox";

interface ChatAreaProps {
    user: User;
    activeConversation: Conversation | null;
    messages: Message[];
    loading: boolean;
    conversationLoading?: boolean;
    error: string;
    onSendMessage: (content: string, attachmentText?: string, imagePreviewUrl?: string) => Promise<void>;
    onStopAgent?: () => void;
    onCancelDocument?: () => void;
    onCreateConversation?: () => void;
    onClearChat: () => void;
    onOpenMobileSidebar: () => void;
    onExtractDocument: (file: File) => Promise<ExtractedDocument | null>;
    documentLoading: boolean;
    documentError: string;
    setDocumentError: (err: string) => void;
}

export const ChatArea: React.FC<ChatAreaProps> = ({
    user,
    activeConversation,
    messages,
    loading,
    error,
    onSendMessage,
    onStopAgent,
    onCancelDocument,
    onClearChat,
    onOpenMobileSidebar,
    onExtractDocument,
    documentLoading,
    documentError,
    setDocumentError,
}) => {
    const [input, setInput] = useState("");
    const [attachedDoc, setAttachedDoc] = useState<ExtractedDocument | null>(null);
    const [attachedImagePreview, setAttachedImagePreview] = useState<string | null>(null);
    const [showExtractedReview, setShowExtractedReview] = useState(false);
    const [lightboxUrl, setLightboxUrl] = useState<string | null>(null);
    const [copiedMsgId, setCopiedMsgId] = useState<number | null>(null);
    const [speakingMsgId, setSpeakingMsgId] = useState<number | null>(null);
    const [isListening, setIsListening] = useState(false);
    const [voiceStatus, setVoiceStatus] = useState("");
    const [isDragOver, setIsDragOver] = useState(false);

    const messagesEndRef = useRef<HTMLDivElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const recognitionRef = useRef<any>(null);

    // Auto-scroll on new messages
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, loading]);

    // Handle auto-resizing textarea
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = "auto";
            textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`;
        }
    }, [input]);

    // Cleanup object URLs on unmount
    useEffect(() => {
        return () => {
            if (attachedImagePreview) {
                URL.revokeObjectURL(attachedImagePreview);
            }
            if (window.speechSynthesis) {
                window.speechSynthesis.cancel();
            }
        };
    }, [attachedImagePreview]);

    // Process file upload (image or PDF)
    const processFile = async (file: File) => {
        setDocumentError("");
        const allowedExtensions = /\.(pdf|jpe?g|png|webp)$/i;
        if (!allowedExtensions.test(file.name)) {
            setDocumentError("Please upload a medical document or image (JPG, PNG, WebP, or PDF).");
            return;
        }
        if (file.size > 10 * 1024 * 1024) {
            setDocumentError("File exceeds 10 MB limit. Please select a smaller file.");
            return;
        }

        // Generate instant local image preview if image
        if (file.type.startsWith("image/")) {
            const previewUrl = URL.createObjectURL(file);
            setAttachedImagePreview(previewUrl);
        } else {
            setAttachedImagePreview(null);
        }

        const extracted = await onExtractDocument(file);
        if (extracted) {
            setAttachedDoc({
                ...extracted,
                file_size_bytes: file.size,
            });
            setShowExtractedReview(true);
        } else {
            setAttachedDoc(null);
        }
    };

    // File input handler
    const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            processFile(file);
        }
        e.target.value = "";
    };

    // Clipboard Paste Listener (Ctrl+V screenshot/photo)
    const handlePaste = (e: React.ClipboardEvent<HTMLTextAreaElement>) => {
        const items = e.clipboardData.items;
        for (let i = 0; i < items.length; i++) {
            if (items[i].type.indexOf("image") !== -1) {
                const file = items[i].getAsFile();
                if (file) {
                    processFile(file);
                    e.preventDefault();
                    break;
                }
            }
        }
    };

    // Drag and Drop
    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragOver(true);
    };

    const handleDragLeave = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragOver(false);
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragOver(false);
        const file = e.dataTransfer.files?.[0];
        if (file) {
            processFile(file);
        }
    };

    // Remove attached document
    const removeAttachment = () => {
        if (attachedImagePreview) {
            URL.revokeObjectURL(attachedImagePreview);
        }
        setAttachedImagePreview(null);
        setAttachedDoc(null);
        setShowExtractedReview(false);
        setDocumentError("");
    };

    // Voice Input (Speech-to-Text)
    const toggleVoiceInput = () => {
        setVoiceStatus("");
        const win = window as any;
        const SpeechRecognition = win.SpeechRecognition || win.webkitSpeechRecognition;

        if (!SpeechRecognition) {
            setVoiceStatus("Voice typing is not supported in this browser.");
            return;
        }

        if (isListening) {
            recognitionRef.current?.stop();
            setIsListening(false);
            return;
        }

        const recognition = new SpeechRecognition();
        recognitionRef.current = recognition;
        recognition.lang = navigator.language || "en-US";
        recognition.interimResults = false;

        recognition.onstart = () => {
            setIsListening(true);
            setVoiceStatus("Listening... speak your question.");
        };

        recognition.onresult = (event: any) => {
            const transcript = event.results[0]?.[0]?.transcript?.trim();
            if (transcript) {
                setInput((prev) => `${prev}${prev.trim() ? " " : ""}${transcript}`);
            }
        };

        recognition.onerror = () => {
            setVoiceStatus("Microphone input error. Please try again.");
            setIsListening(false);
        };

        recognition.onend = () => {
            setIsListening(false);
            setVoiceStatus("");
        };

        try {
            recognition.start();
        } catch {
            setVoiceStatus("Could not start microphone.");
            setIsListening(false);
        }
    };

    // Form Submit
    const handleSend = async (e: React.FormEvent) => {
        e.preventDefault();
        if ((!input.trim() && !attachedDoc) || loading || documentLoading) return;

        const messageToSend = input.trim() || "Please analyze this medical document/image.";
        const attachmentContent = attachedDoc?.extracted_text.trim();
        const previewUrlToSend = attachedImagePreview || undefined;

        setInput("");
        setAttachedDoc(null);
        setAttachedImagePreview(null);
        setShowExtractedReview(false);

        await onSendMessage(messageToSend, attachmentContent, previewUrlToSend);
    };

    // Copy message to clipboard
    const copyToClipboard = (text: string, msgId: number) => {
        navigator.clipboard.writeText(text);
        setCopiedMsgId(msgId);
        setTimeout(() => setCopiedMsgId(null), 2000);
    };

    // Text-to-Speech (TTS)
    const toggleSpeak = (text: string, msgId: number) => {
        if (!window.speechSynthesis) return;

        if (speakingMsgId === msgId) {
            window.speechSynthesis.cancel();
            setSpeakingMsgId(null);
            return;
        }

        window.speechSynthesis.cancel();
        // Clean markdown symbols for cleaner speech
        const plainText = text.replace(/[*#_`~[\]]/g, "").trim();
        const utterance = new SpeechSynthesisUtterance(plainText);
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        utterance.onend = () => setSpeakingMsgId(null);
        utterance.onerror = () => setSpeakingMsgId(null);

        setSpeakingMsgId(msgId);
        window.speechSynthesis.speak(utterance);
    };

    // Export Chat Transcript
    const exportChat = () => {
        if (messages.length === 0) return;
        const transcript = messages
            .map((m) => {
                const role = m.role === "user" ? "PATIENT" : "MEDIASSIST CLINICAL ASSISTANT";
                return `### ${role}\n${m.content}\n`;
            })
            .join("\n---\n\n");

        const blob = new Blob(
            [
                `# MediAssist Clinical Consultation Summary\nDate: ${new Date().toLocaleString()}\nPatient: ${user.full_name}\n\n---\n\n${transcript}`,
            ],
            { type: "text/markdown;charset=utf-8" }
        );
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `MediAssist_Consultation_${Date.now()}.md`;
        a.click();
        URL.revokeObjectURL(url);
    };

    // Detect emergency flag in the latest messages
    const latestEmergency = messages.some(
        (m) =>
            m.role === "assistant" &&
            (m.content.toLowerCase().includes("immediate medical attention") ||
                m.content.toLowerCase().includes("call 911") ||
                m.content.toLowerCase().includes("emergency department") ||
                m.content.toLowerCase().includes("cardiac emergency"))
    );

    return (
        <main
            className={`chat-area-container ${isDragOver ? "drag-active" : ""}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
        >
            {/* Drag Overlay */}
            {isDragOver && (
                <div className="drag-drop-overlay">
                    <Upload size={48} className="text-emerald-500 animate-bounce" />
                    <h3>Drop Medical Image or PDF Here</h3>
                    <p>MediAssist AI Vision will automatically analyze the clinical content.</p>
                </div>
            )}

            {/* Chat Top Header */}
            <header className="chat-top-header">
                <div className="header-left">
                    <button
                        type="button"
                        className="btn-icon mobile-menu-btn"
                        onClick={onOpenMobileSidebar}
                        aria-label="Toggle Sidebar"
                    >
                        <Menu size={20} />
                    </button>

                    <div className="header-title-box">
                        <div className="online-indicator"></div>
                        <h2>{activeConversation ? activeConversation.title : "MediAssist Clinical AI"}</h2>
                    </div>
                </div>

                <div className="header-actions">
                    {messages.length > 0 && (
                        <>
                            <button
                                type="button"
                                className="btn btn-sm btn-ghost"
                                onClick={exportChat}
                                title="Export chat transcript"
                            >
                                <Download size={15} />
                                <span className="btn-text-desktop">Export</span>
                            </button>
                            <button
                                type="button"
                                className="btn btn-sm btn-ghost text-red-500"
                                onClick={onClearChat}
                                title="Clear conversation"
                            >
                                <Trash2 size={15} />
                                <span className="btn-text-desktop">Clear</span>
                            </button>
                        </>
                    )}
                </div>
            </header>

            {/* Emergency Notice Alert */}
            {latestEmergency && (
                <div className="emergency-callout-banner" role="alert">
                    <div className="callout-content">
                        <AlertTriangle size={24} className="text-red-500 flex-shrink-0" />
                        <div>
                            <strong>CRITICAL EMERGENCY TRIAGE NOTICE</strong>
                            <p>Symptoms discussed may require immediate urgent medical care. Do not delay.</p>
                        </div>
                    </div>
                    <a href="tel:911" className="btn btn-emergency">
                        <PhoneCall size={16} />
                        <span>Call 911 / 112 Now</span>
                    </a>
                </div>
            )}

            {/* Messages Scroll Area */}
            <div className="messages-stream">
                {error && (
                    <div className="alert-box alert-error" role="alert">
                        <AlertTriangle size={16} />
                        <span>{error}</span>
                    </div>
                )}

                {!activeConversation || messages.length === 0 ? (
                    <div className="welcome-hero-card">
                        <div className="welcome-badge">
                            <Stethoscope size={28} className="text-emerald-500" />
                        </div>
                        <h1>Hello, {user.full_name} 👋</h1>
                        <p className="welcome-tagline">
                            I am your clinical intelligence assistant. You can upload doctor prescriptions,
                            lab reports, describe symptoms, or ask health questions.
                        </p>

                        <div className="starter-chips-grid">
                            <button
                                type="button"
                                className="starter-chip"
                                onClick={() => fileInputRef.current?.click()}
                            >
                                <div className="chip-icon bg-emerald">
                                    <Camera size={18} />
                                </div>
                                <div className="chip-text">
                                    <strong>Analyze Prescription or Report</strong>
                                    <span>Upload an image or PDF for AI Vision breakdown</span>
                                </div>
                            </button>

                            <button
                                type="button"
                                className="starter-chip"
                                onClick={() =>
                                    setInput("What are common warning signs of high blood pressure, and how should it be monitored?")
                                }
                            >
                                <div className="chip-icon bg-blue">
                                    <HeartPulse size={18} />
                                </div>
                                <div className="chip-text">
                                    <strong>Cardiovascular Health</strong>
                                    <span>Ask about BP guidelines and normal ranges</span>
                                </div>
                            </button>

                            <button
                                type="button"
                                className="starter-chip"
                                onClick={() =>
                                    setInput("Help me prepare 5 important questions to ask my physician during my annual checkup.")
                                }
                            >
                                <div className="chip-icon bg-purple">
                                    <FileText size={18} />
                                </div>
                                <div className="chip-text">
                                    <strong>Doctor Visit Prep</strong>
                                    <span>Generate personalized appointment questions</span>
                                </div>
                            </button>

                            <button
                                type="button"
                                className="starter-chip"
                                onClick={() =>
                                    setInput("Explain the difference between Type 1 and Type 2 diabetes in simple terms.")
                                }
                            >
                                <div className="chip-icon bg-teal">
                                    <Sparkles size={18} />
                                </div>
                                <div className="chip-text">
                                    <strong>Clinical Explanations</strong>
                                    <span>Clarify medical diagnoses and lab terminology</span>
                                </div>
                            </button>
                        </div>
                    </div>
                ) : (
                    messages.map((m) => {
                        const isAssistant = m.role === "assistant";
                        const isSpeaking = speakingMsgId === m.id;
                        const isCopied = copiedMsgId === m.id;

                        return (
                            <div
                                key={m.id}
                                className={`message-bubble-row ${isAssistant ? "assistant-row" : "user-row"}`}
                            >
                                <div className="bubble-avatar">
                                    {isAssistant ? (
                                        <Stethoscope size={18} />
                                    ) : (
                                        user.full_name.slice(0, 2).toUpperCase()
                                    )}
                                </div>

                                <div className="bubble-body">
                                    <div className="bubble-sender-bar">
                                        <span className="sender-name">
                                            {isAssistant ? "MediAssist" : user.full_name}
                                        </span>
                                        {m.created_at && (
                                            <span className="msg-time">
                                                {new Date(m.created_at).toLocaleTimeString([], {
                                                    hour: "2-digit",
                                                    minute: "2-digit",
                                                })}
                                            </span>
                                        )}
                                    </div>

                                    {/* Uploaded Image Thumbnail in User Message */}
                                    {m.image_preview_url && (
                                        <div
                                            className="attached-image-card"
                                            onClick={() => setLightboxUrl(m.image_preview_url || null)}
                                            title="Click to view full image"
                                        >
                                            <img
                                                src={m.image_preview_url}
                                                alt={m.attachment_name || "Uploaded medical document"}
                                                className="attached-thumb"
                                            />
                                            <div className="thumb-hover-overlay">
                                                <Eye size={18} />
                                                <span>Expand View</span>
                                            </div>
                                        </div>
                                    )}

                                    {/* Message Text Markdown */}
                                    <div className="markdown-prose">
                                        <ReactMarkdown>{m.content}</ReactMarkdown>
                                    </div>

                                    {/* Verified Source Citations */}
                                    {isAssistant && m.sources && m.sources.length > 0 && (
                                        <div className="source-citations-container">
                                            <span className="citations-header">
                                                <Sparkles size={13} className="text-emerald-500" />
                                                <span>Verified Medical Citations ({m.sources.length})</span>
                                            </span>
                                            <div className="citations-grid">
                                                {m.sources.map((s, idx) => (
                                                    <div key={idx} className="citation-pill">
                                                        <FileText size={12} className="citation-icon" />
                                                        <div className="citation-details">
                                                            {s.url ? (
                                                                <a
                                                                    href={s.url}
                                                                    target="_blank"
                                                                    rel="noreferrer"
                                                                    className="citation-link"
                                                                >
                                                                    {s.title}
                                                                </a>
                                                            ) : (
                                                                <span className="citation-title">{s.title}</span>
                                                            )}
                                                            <span className="citation-meta">
                                                                {s.source}
                                                                {s.page ? ` (p. ${s.page})` : ""}
                                                            </span>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {/* Assistant Action Bar */}
                                    {isAssistant && (
                                        <div className="message-action-bar">
                                            <button
                                                type="button"
                                                className="action-pill-btn"
                                                onClick={() => copyToClipboard(m.content, m.id)}
                                                title="Copy message"
                                            >
                                                {isCopied ? (
                                                    <>
                                                        <Check size={14} className="text-emerald-500" />
                                                        <span>Copied!</span>
                                                    </>
                                                ) : (
                                                    <>
                                                        <Copy size={14} />
                                                        <span>Copy</span>
                                                    </>
                                                )}
                                            </button>

                                            <button
                                                type="button"
                                                className={`action-pill-btn ${isSpeaking ? "active-speaker" : ""}`}
                                                onClick={() => toggleSpeak(m.content, m.id)}
                                                title={isSpeaking ? "Stop listening" : "Listen to response"}
                                            >
                                                {isSpeaking ? (
                                                    <>
                                                        <VolumeX size={14} className="text-red-500" />
                                                        <span>Stop</span>
                                                    </>
                                                ) : (
                                                    <>
                                                        <Volume2 size={14} />
                                                        <span>Listen</span>
                                                    </>
                                                )}
                                            </button>
                                        </div>
                                    )}
                                </div>
                            </div>
                        );
                    })
                )}

                {/* Loading / Typing Indicator with Stop Action */}
                {loading && (
                    <div className="message-bubble-row assistant-row typing-row">
                        <div className="bubble-avatar">
                            <Stethoscope size={18} />
                        </div>
                        <div className="bubble-body typing-body-with-stop">
                            <div className="typing-dots">
                                <span className="dot"></span>
                                <span className="dot"></span>
                                <span className="dot"></span>
                            </div>
                            <span className="typing-label">Consulting medical literature & synthesizing...</span>
                            {onStopAgent && (
                                <button
                                    type="button"
                                    className="btn-stop-pill"
                                    onClick={onStopAgent}
                                    title="Stop generation"
                                >
                                    <Square size={11} className="fill-current" />
                                    <span>Stop Agent</span>
                                </button>
                            )}
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {/* Input Composer Tray */}
            <div className="composer-container">
                {/* Hidden File Input */}
                <input
                    ref={fileInputRef}
                    type="file"
                    className="hidden"
                    accept=".pdf,.jpg,.jpeg,.png,.webp,application/pdf,image/jpeg,image/png,image/webp"
                    onChange={handleFileInput}
                    disabled={loading || documentLoading}
                />

                {/* Document / Image Extracting State */}
                {documentLoading && (
                    <div className="attachment-loading-bar">
                        <Loader2 size={18} className="animate-spin text-emerald-500" />
                        <span>Analyzing document with Gemini AI Multimodal Vision...</span>
                        {onCancelDocument && (
                            <button
                                type="button"
                                className="btn-stop-sm"
                                onClick={onCancelDocument}
                                title="Cancel document analysis"
                            >
                                Cancel
                            </button>
                        )}
                    </div>
                )}

                {/* Document Error Display */}
                {documentError && (
                    <div className="alert-box alert-error mb-2">
                        <AlertTriangle size={15} />
                        <span>{documentError}</span>
                        <button
                            type="button"
                            className="ml-auto text-xs"
                            onClick={() => setDocumentError("")}
                        >
                            <X size={14} />
                        </button>
                    </div>
                )}

                {/* Attached Document & Vision Preview Bar */}
                {attachedDoc && (
                    <div className="attachment-preview-card">
                        <div className="preview-top">
                            {attachedImagePreview ? (
                                <img
                                    src={attachedImagePreview}
                                    alt="Preview"
                                    className="thumb-mini"
                                    onClick={() => setLightboxUrl(attachedImagePreview)}
                                    title="Click to view full image"
                                />
                            ) : (
                                <div className="pdf-mini-badge">
                                    <FileText size={20} className="text-emerald-500" />
                                </div>
                            )}

                            <div className="attachment-details">
                                <span className="attachment-filename">{attachedDoc.filename}</span>
                                <div className="attachment-badges">
                                    <span className="badge-vision-ready">
                                        <Sparkles size={11} />
                                        <span>AI Vision Ready</span>
                                    </span>
                                    {attachedDoc.file_size_bytes && (
                                        <span className="attachment-filesize">
                                            {Math.round(attachedDoc.file_size_bytes / 1024)} KB
                                        </span>
                                    )}
                                </div>
                            </div>

                            <div className="attachment-actions">
                                <button
                                    type="button"
                                    className="btn btn-xs btn-ghost"
                                    onClick={() => setShowExtractedReview(!showExtractedReview)}
                                >
                                    {showExtractedReview ? "Hide Details" : "Review Extracted Text"}
                                </button>
                                <button
                                    type="button"
                                    className="btn-icon remove-attachment-btn"
                                    onClick={removeAttachment}
                                    title="Remove attachment"
                                    aria-label="Remove attachment"
                                >
                                    <X size={16} />
                                </button>
                            </div>
                        </div>

                        {/* Collapsible Extracted Details */}
                        {showExtractedReview && (
                            <div className="extracted-review-box">
                                <label htmlFor="extracted-review-textarea">
                                    Extracted clinical context (attached automatically to your question):
                                </label>
                                <textarea
                                    id="extracted-review-textarea"
                                    value={attachedDoc.extracted_text}
                                    onChange={(e) =>
                                        setAttachedDoc({ ...attachedDoc, extracted_text: e.target.value })
                                    }
                                    maxLength={40000}
                                />
                            </div>
                        )}
                    </div>
                )}

                {/* Voice Status Alert */}
                {voiceStatus && (
                    <div className="voice-status-pill">
                        <Mic size={14} className={isListening ? "text-red-500 animate-pulse" : ""} />
                        <span>{voiceStatus}</span>
                    </div>
                )}

                {/* Composer Form */}
                <form onSubmit={handleSend} className="composer-form">
                    <div className="composer-inner">
                        <button
                            type="button"
                            className="composer-action-btn"
                            onClick={() => fileInputRef.current?.click()}
                            disabled={loading || documentLoading}
                            title="Attach medical prescription, lab report, or symptom image"
                            aria-label="Attach medical document or image"
                        >
                            <Paperclip size={19} />
                        </button>

                        <button
                            type="button"
                            className={`composer-action-btn ${isListening ? "listening-active" : ""}`}
                            onClick={toggleVoiceInput}
                            disabled={loading || documentLoading}
                            title={isListening ? "Stop listening" : "Voice typing"}
                            aria-label="Voice input"
                        >
                            {isListening ? (
                                <MicOff size={19} className="text-red-500" />
                            ) : (
                                <Mic size={19} />
                            )}
                        </button>

                        <textarea
                            ref={textareaRef}
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onPaste={handlePaste}
                            onKeyDown={(e) => {
                                if (e.key === "Enter" && !e.shiftKey) {
                                    e.preventDefault();
                                    handleSend(e);
                                }
                            }}
                            placeholder={
                                attachedDoc
                                    ? "Add questions about this document (or press Enter to analyze)..."
                                    : "Ask a health question, describe symptoms, or paste an image (Ctrl+V)..."
                            }
                            rows={1}
                            maxLength={10000}
                            disabled={loading || documentLoading}
                        />

                        {loading ? (
                            <button
                                type="button"
                                className="btn btn-stop-agent"
                                onClick={onStopAgent}
                                title="Stop generating response"
                                aria-label="Stop generating response"
                            >
                                <Square size={14} className="fill-current" />
                                <span>Stop</span>
                            </button>
                        ) : (
                            <button
                                type="submit"
                                className="btn btn-primary btn-send"
                                disabled={
                                    (!input.trim() && !attachedDoc) ||
                                    documentLoading
                                }
                                title="Send Message (Enter)"
                                aria-label="Send Message"
                            >
                                <Send size={18} />
                            </button>
                        )}
                    </div>

                    <div className="composer-footer-note">
                        <span>
                            MediAssist AI provides general health information. Not a substitute for
                            professional medical advice or emergency care.
                        </span>
                    </div>
                </form>
            </div>

            {/* Image Lightbox Modal */}
            {lightboxUrl && (
                <ImageLightbox
                    imageUrl={lightboxUrl}
                    altText="Medical document preview"
                    onClose={() => setLightboxUrl(null)}
                />
            )}
        </main>
    );
};
