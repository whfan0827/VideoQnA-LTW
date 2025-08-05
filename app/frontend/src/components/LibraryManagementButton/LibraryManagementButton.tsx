import { Text } from "@fluentui/react";
import { Folder24Regular } from "@fluentui/react-icons";

import styles from "./LibraryManagementButton.module.css";

interface Props {
    className?: string;
    onClick: () => void;
}

export const LibraryManagementButton = ({ className, onClick }: Props) => {
    return (
        <div className={`${styles.container} ${className ?? ""}`} onClick={onClick}>
            <Folder24Regular />
            <Text>Library Management</Text>
        </div>
    );
};
