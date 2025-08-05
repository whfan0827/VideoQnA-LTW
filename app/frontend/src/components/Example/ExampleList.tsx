import { useState, useEffect } from "react";
import { Example } from "./Example";

import styles from "./Example.module.css";

export type ExampleModel = {
    text: string;
    value: string;
};

const DEFAULT_EXAMPLES: ExampleModel[] = [
    {
        text: "What insights are included with Azure AI Video Indexer?",
        value: "What insights are included with Azure AI Video Indexer?"
    },
    {
        text: "What is OCR?",
        value: "What is OCR?"
    },
    {
        text: "What is the distance to Mars?",
        value: "What is the distance to Mars?"
    }
];



interface Props {
    onExampleClicked: (value: string) => void;
}

export const ExampleList = ({ onExampleClicked }: Props) => {
    const [examples, setExamples] = useState<ExampleModel[]>(DEFAULT_EXAMPLES);

    // Load custom starters from localStorage
    const loadCustomStarters = () => {
        try {
            const saved = localStorage.getItem('conversation_starters');
            if (saved) {
                const customStarters = JSON.parse(saved) as ExampleModel[];
                if (customStarters.length > 0) {
                    setExamples(customStarters);
                    return;
                }
            }
        } catch (error) {
            console.error('Error loading custom starters:', error);
        }
        setExamples(DEFAULT_EXAMPLES);
    };

    useEffect(() => {
        loadCustomStarters();

        // Listen for updates from Developer Settings
        const handleUpdate = () => {
            loadCustomStarters();
        };

        window.addEventListener('conversation_starters_updated', handleUpdate);
        return () => {
            window.removeEventListener('conversation_starters_updated', handleUpdate);
        };
    }, []);

    return (
        <ul className={styles.examplesNavList}>
            {examples.map((x, i) => (
                <li className={styles.examplesNavListItem} key={i}>
                    <Example text={x.text} value={x.value} onClick={onExampleClicked} />
                </li>
            ))}
        </ul>
    );
};