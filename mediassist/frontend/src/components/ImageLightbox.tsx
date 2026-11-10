import React from "react";
import { X, ZoomIn, ZoomOut, Download } from "lucide-react";

interface ImageLightboxProps {
    imageUrl: string;
    altText?: string;
    onClose: () => void;
}

export const ImageLightbox: React.FC<ImageLightboxProps> = ({
    imageUrl,
    altText = "Medical document preview",
    onClose,
}) => {
    const [zoom, setZoom] = React.useState(1);

    const handleZoomIn = () => setZoom((prev) => Math.min(prev + 0.25, 3));
    const handleZoomOut = () => setZoom((prev) => Math.max(prev - 0.25, 0.5));

    return (
        <div className="lightbox-overlay" onClick={onClose} role="dialog" aria-modal="true">
            <div className="lightbox-container" onClick={(e) => e.stopPropagation()}>
                <div className="lightbox-header">
                    <span className="lightbox-title">{altText}</span>
                    <div className="lightbox-controls">
                        <button
                            type="button"
                            className="lightbox-btn"
                            onClick={handleZoomOut}
                            title="Zoom out"
                            aria-label="Zoom out"
                        >
                            <ZoomOut size={18} />
                        </button>
                        <span className="lightbox-zoom-val">{Math.round(zoom * 100)}%</span>
                        <button
                            type="button"
                            className="lightbox-btn"
                            onClick={handleZoomIn}
                            title="Zoom in"
                            aria-label="Zoom in"
                        >
                            <ZoomIn size={18} />
                        </button>
                        <a
                            href={imageUrl}
                            download={altText}
                            className="lightbox-btn"
                            title="Download image"
                            aria-label="Download image"
                        >
                            <Download size={18} />
                        </a>
                        <button
                            type="button"
                            className="lightbox-btn close-btn"
                            onClick={onClose}
                            title="Close preview"
                            aria-label="Close preview"
                        >
                            <X size={20} />
                        </button>
                    </div>
                </div>
                <div className="lightbox-content">
                    <img
                        src={imageUrl}
                        alt={altText}
                        style={{ transform: `scale(${zoom})` }}
                        className="lightbox-img"
                    />
                </div>
            </div>
        </div>
    );
};

