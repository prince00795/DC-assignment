#pragma once

#include "generator/data_generator.hpp"
#include "pipeline/bridge.hpp"
#include <string>

namespace dc {
namespace cli {

class MenuController {
public:
    MenuController();

    void run_interactive();
    void show_help_guide() const;

private:
    std::string current_bitstream_;
    generator::DataGenerator generator_;
    pipeline::PipelineBridge bridge_;

    void menu_generator();
    void menu_palindrome();
    void menu_line_coding();
    void menu_scrambling();
    void menu_analog_pcm();
    void menu_delta_modulation();
    void menu_pipeline();
};

} // namespace cli
} // namespace dc
