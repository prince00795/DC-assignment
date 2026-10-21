#include "cli/menu.hpp"
#include "cli/report.hpp"
#include <iostream>
#include <string>

int main(int argc, char* argv[]) {
    if (argc > 1) {
        std::string arg = argv[1];
        if (arg == "--audit" || arg == "--report") {
            dc::cli::SystemReport::generate_audit_report();
            return 0;
        } else if (arg == "--help" || arg == "-h") {
            dc::cli::MenuController menu;
            menu.show_help_guide();
            return 0;
        } else if (arg == "--demo") {
            std::cout << "[Demo Mode] Executing full pipeline and generating report...\n";
            dc::cli::SystemReport::generate_audit_report();
            std::cout << "[Opening Visualizer] Launching interactive dashboard in browser...\n";
            system("start visualizer\\index.html");
            return 0;
        } else if (arg == "--gui" || arg == "--web" || arg == "--visual") {
            std::cout << "[Visualizer] Launching interactive studio in default browser...\n";
            system("start visualizer\\index.html");
            return 0;
        }
    }

    dc::cli::MenuController menu;
    menu.run_interactive();
    return 0;
}
