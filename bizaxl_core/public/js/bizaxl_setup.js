/**
 * BizAxl Module Selection Step
 * Injected into ERPNext Setup Wizard
 */

frappe.setup.on("before_load", function() {
    // Add BizAxl step to setup wizard
    frappe.setup.slides_settings.push({
        name: "bizaxl_modules",
        title: __("Configure Modules"),
        icon: "fa fa-th-large",
        help: __("Select which ERPNext modules you want to enable. Core modules (Accounting, Buying, Selling) are always enabled."),

        before_load: function() {
            var slide = this;
            slide.module_config = null;

            // Load module config from server
            frappe.call({
                method: "bizaxl_core.api.module_manager.get_module_config",
                callback: function(r) {
                    if (r.message) {
                        slide.module_config = r.message;
                        slide.render_modules();
                    }
                }
            });
        },

        render_modules: function() {
            var slide = this;
            var config = slide.module_config;
            if (!config) return;

            var html = '<div style="font-family:-apple-system,sans-serif">';

            // App profile selector
            if (config.profiles && config.profiles.length > 0) {
                html += '<div style="margin-bottom:20px">';
                html += '<label style="font-weight:600;font-size:13px;color:#333">Quick Setup — Select your app:</label>';
                html += '<div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:8px">';
                config.profiles.forEach(function(p) {
                    html += '<button class="bizaxl-profile-btn" data-profile="' + p.app_name + '" ';
                    html += 'style="padding:6px 14px;border-radius:20px;border:2px solid #dee2e6;';
                    html += 'background:white;cursor:pointer;font-size:12px;font-weight:500;transition:all 0.15s">';
                    html += p.display_name || p.app_name;
                    html += '</button>';
                });
                html += '</div></div>';
            }

            // Core modules (always on)
            html += '<div style="margin-bottom:20px">';
            html += '<label style="font-weight:600;font-size:13px;color:#333">✅ Core Modules (always enabled):</label>';
            html += '<div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:8px">';
            config.core_modules.forEach(function(m) {
                html += '<span style="padding:4px 10px;border-radius:12px;background:#e8f5e9;';
                html += 'color:#2e7d32;font-size:11px;font-weight:500">';
                html += m.icon + ' ' + m.label + '</span>';
            });
            html += '</div></div>';

            // Optional modules
            if (config.optional_modules && config.optional_modules.length > 0) {
                html += '<div>';
                html += '<label style="font-weight:600;font-size:13px;color:#333">Optional Modules:</label>';
                html += '<p style="font-size:11px;color:#666;margin:4px 0 10px">Check the modules you need:</p>';
                html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">';

                config.optional_modules.forEach(function(m) {
                    var isChecked = !config.hidden_by_default.includes(m.module);
                    html += '<label style="display:flex;align-items:flex-start;gap:8px;';
                    html += 'padding:10px;border-radius:8px;border:1px solid #dee2e6;cursor:pointer;';
                    html += 'background:white;transition:all 0.15s" class="bizaxl-module-card">';
                    html += '<input type="checkbox" class="bizaxl-module-check" ';
                    html += 'data-module="' + m.module + '" ';
                    html += (isChecked ? 'checked' : '') + ' ';
                    html += 'style="margin-top:2px;width:14px;height:14px;accent-color:#00e5a0">';
                    html += '<div>';
                    html += '<div style="font-size:12px;font-weight:600;color:#333">' + m.icon + ' ' + m.label + '</div>';
                    if (m.description) {
                        html += '<div style="font-size:10px;color:#888;margin-top:2px">' + m.description + '</div>';
                    }
                    html += '</div></label>';
                });
                html += '</div></div>';
            }

            html += '</div>';

            // Render into slide
            var container = slide.$body || slide.$slide;
            if (container) {
                container.html(html);

                // Wire profile buttons
                container.on("click", ".bizaxl-profile-btn", function() {
                    var profileName = $(this).data("profile");
                    var profile = config.profiles.find(p => p.app_name === profileName);
                    if (!profile) return;

                    // Update checkboxes based on profile
                    container.find(".bizaxl-module-check").each(function() {
                        var module = $(this).data("module");
                        var shouldShow = profile.show_modules && profile.show_modules.includes(module);
                        var isOptional = profile.optional_modules &&
                            profile.optional_modules.some(m =>
                                (typeof m === "string" ? m : m.module) === module
                            );
                        $(this).prop("checked", shouldShow || isOptional);
                    });

                    // Highlight selected profile
                    container.find(".bizaxl-profile-btn").css({
                        "border-color": "#dee2e6", "background": "white", "color": "#333"
                    });
                    $(this).css({
                        "border-color": "#00e5a0", "background": "#e8fdf5", "color": "#00a070"
                    });
                });

                // Wire checkbox styling
                container.on("change", ".bizaxl-module-check", function() {
                    var card = $(this).closest(".bizaxl-module-card");
                    if ($(this).is(":checked")) {
                        card.css({"border-color": "#00e5a0", "background": "#f0fff8"});
                    } else {
                        card.css({"border-color": "#dee2e6", "background": "white"});
                    }
                });
            }
        },

        get_values: function() {
            // Collect selected modules
            var selected = [];
            $(".bizaxl-module-check:checked").each(function() {
                selected.push($(this).data("module"));
            });
            return {bizaxl_selected_modules: JSON.stringify(selected)};
        },

        validate: function() {
            return true; // Always valid — core modules are always enabled
        }
    });
});
