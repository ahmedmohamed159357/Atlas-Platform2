import React, { useState, useEffect } from 'react';

interface CyberTextProps {
    text: string;
    speed?: number;
    scrambleSpeed?: number;
    delay?: number;
    className?: string;
}

const CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%&*";

const CyberText: React.FC<CyberTextProps> = ({
    text,
    speed = 50,
    scrambleSpeed = 30,
    delay = 0,
    className = ""
}) => {
    const [display, setDisplay] = useState("");
    const [started, setStarted] = useState(false);

    useEffect(() => {
        const timeout = setTimeout(() => setStarted(true), delay);
        return () => clearTimeout(timeout);
    }, [delay]);

    useEffect(() => {
        if (!started) return;

        let currentIndex = 0;
        let scrambleInterval: ReturnType<typeof setInterval>;

        const interval = setInterval(() => {
            if (currentIndex >= text.length) {
                clearInterval(interval);
                return;
            }

            // Scramble effect for the current character being revealed
            let scrambleCount = 0;
            scrambleInterval = setInterval(() => {
                const randomChar = CHARS[Math.floor(Math.random() * CHARS.length)];
                setDisplay(prev => prev.substring(0, currentIndex) + randomChar);
                scrambleCount++;
                if (scrambleCount > 3) clearInterval(scrambleInterval);
            }, scrambleSpeed);

            // Finalize character
            setTimeout(() => {
                setDisplay(prev => text.substring(0, currentIndex + 1));
                currentIndex++;
            }, speed);

        }, speed);

        return () => {
            clearInterval(interval);
            clearInterval(scrambleInterval);
        };
    }, [started, text, speed, scrambleSpeed]);

    return <span className={`font-mono text-neon-green ${className}`}>{display}</span>;
};

export default CyberText;
