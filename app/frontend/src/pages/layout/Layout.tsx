import { Outlet, Link } from "react-router-dom";

import styles from "./Layout.module.css";

const Layout = () => {
    return (
        <div className={styles.layout}>
            <header className={styles.header} role={"banner"}>
                <div className={styles.headerContainer}>
                    <Link to="/" className={styles.headerTitleContainer}>
                        <h3 className={styles.headerTitle}>AI-powered search | Video</h3>
                    </Link>
                    <h4 className={styles.headerRightText}>Powered by Logicalis Taiwan BD-CIS</h4>
                </div>
            </header>

            <Outlet />
            <footer className={styles.footer}>
                <div className={styles.footerText}>
                    © vincent.fan@ap.logicalis.com, Logicalis Taiwan
                </div>
            </footer>
        </div>
    );
};

export default Layout;
