import { Text } from "@fluentui/react";
import { Chat24Regular } from "@fluentui/react-icons";

import styles from "./ConversationSettingsButton.module.css";

interface Props {
    className?: string;
    onClick: () => void;
}

export const ConversationSettingsButton = ({ className, onClick }: Props) => {
    return (
        <div className={`${styles.container} ${className ?? ""}`} onClick={onClick}>
            <Chat24Regular />
            <Text>Conversation Settings</Text>
        </div>
    );
};