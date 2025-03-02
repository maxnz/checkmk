/**
 * Copyright (C) 2019 Checkmk GmbH - License: GNU General Public License v2
 * This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
 * conditions defined in the file COPYING, which is part of this source code package.
 */

import * as d3 from "d3";
import {Simulation} from "d3";
import {compute_node_positions_from_list_of_nodes} from "nodevis/layout";
import {StyleOptionSpecRange, StyleOptionValues} from "nodevis/layout_utils";
import {NodevisLink, NodevisNode, NodevisWorld} from "nodevis/type_defs";

export type SimulationForce =
    | "charge"
    | "collide"
    | "center"
    | "link_distance"
    | "link_strength";

export class ForceSimulation {
    _world: NodevisWorld;
    _simulation: Simulation<NodevisNode, NodevisLink>;
    _last_gui_update_duration = 0;
    _all_nodes: NodevisNode[] = [];
    _all_links: NodevisLink[] = [];
    _force_config: ForceConfig;

    constructor(world: NodevisWorld, force_config_class: typeof ForceConfig) {
        this._world = world;
        this._simulation = d3.forceSimulation<NodevisNode>();
        this._simulation.stop();
        this._simulation.alpha(0);
        this._simulation.alphaMin(0.1);
        this._simulation.on("tick", () => this.tick_called());
        this._simulation.on("end", () => this._simulation_end());
        this._force_config = new force_config_class(this);
        this.setup_forces();
    }

    set_force_options(force_options: ForceOptions): void {
        this._force_config.options = force_options;
    }

    get_force_options(): ForceOptions {
        return this._force_config.options;
    }

    show_force_config() {
        this._world.layout_manager.toolbar_plugin
            .layout_style_configuration()
            .show_configuration(
                "force",
                this._force_config.get_style_options(),
                this._force_config.options,
                (event: d3.D3DragEvent<any, any, any>, options) =>
                    this._force_config.changed_options(event, options),
                event => {
                    this._force_config.changed_options(
                        event,
                        this._force_config.get_default_options()
                    );
                    this.show_force_config();
                }
            );
    }

    set_force_config_class(force_config_class: typeof ForceConfig) {
        this._force_config = new force_config_class(this);
    }

    tick_called(): void {
        if (!this._world.viewport) return;

        // GUI updates with hundreds of nodes might cause rendering stress
        // The laggy_rendering_limit (ms) throttles the visual update to a reasonable amount
        // When the simulation is finished, a final visual update is started anyway.
        const laggy_rendering_limit = 10;
        if (this._last_gui_update_duration > laggy_rendering_limit) {
            this._last_gui_update_duration -= laggy_rendering_limit;
            return;
        }
        this._last_gui_update_duration = this._update_gui();
    }

    _simulation_end(): void {
        //console.log("simulation end");
        if (!this._world.viewport) return;
        this._update_gui();
        this._world.layout_manager.simulation_end_actions();
    }

    _update_gui(): number {
        const update_start = window.performance.now();
        this._enforce_free_float_styles_retranslation();
        compute_node_positions_from_list_of_nodes(this._get_force_nodes());
        this._world.viewport.update_gui_of_layers();
        return window.performance.now() - update_start;
    }

    _get_force_nodes(): NodevisNode[] {
        const force_nodes: NodevisNode[] = [];
        this._world.viewport.get_hierarchy_list().forEach(chunk => {
            chunk.nodes.forEach(node => {
                if (node.data.current_positioning.free) force_nodes.push(node);
            });
        });
        return force_nodes;
    }

    _enforce_free_float_styles_retranslation(): void {
        for (const idx in this._world.layout_manager._active_styles) {
            const style = this._world.layout_manager._active_styles[idx];
            if (!style.has_fixed_position() && style.type() != "force") {
                style.force_style_translation();
                style.translate_coords();
                compute_node_positions_from_list_of_nodes(
                    style.filtered_descendants
                );
                style.filtered_descendants.forEach(
                    node => (node.use_transition = false)
                );
            }
        }
    }

    restart_with_alpha(alpha: number): void {
        if (this._simulation.alpha() < 0.12) this._simulation.restart();
        this._simulation.alpha(alpha);
    }

    update_nodes_and_links(
        all_nodes: NodevisNode[],
        all_links: NodevisLink[]
    ): void {
        this._all_nodes = all_nodes;
        this._all_links = all_links;
        this._simulation.nodes(this._all_nodes);
        this.setup_forces();
    }

    setup_forces(): void {
        this._update_charge_force();
        this._update_collision_force();
        this._update_center_force();
        this._update_link_force();
    }

    _compute_force(node: NodevisNode, force_name: SimulationForce): number {
        const gui_node = this._world.nodes_layer.get_node_by_id(node.data.id);
        if (gui_node == null) return 0;
        return gui_node.get_force(force_name, this._force_config.options);
    }

    _update_charge_force(): void {
        const charge_force = d3
            .forceManyBody<NodevisNode>()
            .strength(node => {
                return this._compute_force(node, "charge");
            })
            .distanceMax(800);
        this._simulation.force("charge_force", charge_force);
    }

    _update_collision_force(): void {
        const collide_force = d3.forceCollide<NodevisNode>(node => {
            return this._compute_force(node, "collide");
        });
        this._simulation.force("collide", collide_force);
    }

    _update_center_force(): void {
        const forceX = d3
            .forceX<NodevisNode>(d => {
                // X Position is currently fixed
                return d.data.chunk.coords.x + d.data.chunk.coords.width / 2;
            })
            .strength(d => {
                return this._compute_force(d, "center");
            });

        const forceY = d3
            .forceY<NodevisNode>(d => {
                // Y Position is currently fixed
                return d.data.chunk.coords.y + d.data.chunk.coords.height / 2;
            })
            .strength(d => {
                return this._compute_force(d, "center");
            });
        this._simulation.force("x", forceX);
        this._simulation.force("y", forceY);
    }

    _update_link_force(): void {
        const link_force = d3
            .forceLink<NodevisNode, NodevisLink>(this._all_links)
            .id(function (d) {
                return d.data.id;
            })
            .distance(d => {
                return this._compute_force(d.source, "link_distance");
            })
            .strength(d => {
                return this._compute_force(d.source, "link_strength");
            });
        this._simulation.force("links", link_force);
    }
}

//#.
//#   .-Force--------------------------------------------------------------.
//#   |                       _____                                        |
//#   |                      |  ___|__  _ __ ___ ___                       |
//#   |                      | |_ / _ \| '__/ __/ _ \                      |
//#   |                      |  _| (_) | | | (_|  __/                      |
//#   |                      |_|  \___/|_|  \___\___|                      |
//#   |                                                                    |
//#   +--------------------------------------------------------------------+

export type ForceOptions = {
    charge: number;
    center: number;
    collide: number;
    link_distance: number;
    link_strength: number;
    [name: string]: number;
};

export class ForceConfig {
    _force_simulation: ForceSimulation;
    options: ForceOptions;
    description = "Force configuration";

    constructor(
        force_simulation: ForceSimulation,
        options: ForceOptions | null = null
    ) {
        this._force_simulation = force_simulation;
        if (options == null) options = this.get_default_options();
        this.options = options;
    }

    get_default_options(): ForceOptions {
        const default_options: ForceOptions = {} as ForceOptions;
        this.get_style_options().forEach(option => {
            default_options[option.id] = option.values.default;
        });
        return default_options;
    }

    changed_options(
        _event: d3.D3DragEvent<any, any, any>,
        new_options: StyleOptionValues
    ) {
        this.options = new_options as ForceOptions;
        this._force_simulation.setup_forces();
        this._force_simulation.restart_with_alpha(0.5);
    }

    get_style_options(): StyleOptionSpecRange[] {
        return [
            {
                id: "center",
                values: {default: 0.05, min: -0.08, max: 1, step: 0.01},
                option_type: "range",
                text: "Center force strength",
            },
            {
                id: "charge",
                values: {default: -300, min: -1000, max: 50, step: 1},
                option_type: "range",
                text: "Repulsion force",
            },
            {
                id: "link_distance",
                values: {default: 30, min: -10, max: 500, step: 1},
                option_type: "range",
                text: "Link distance",
            },
            {
                id: "link_strength",
                values: {default: 0.3, min: 0, max: 4, step: 0.01},
                option_type: "range",
                text: "Link strength",
            },
            {
                id: "collide",
                values: {default: 15, min: 0, max: 150, step: 1},
                option_type: "range",
                text: "Collision box",
            },
        ];
    }
}

export class BIForceConfig extends ForceConfig {
    override description = "BI Force configuration";

    override get_style_options(): StyleOptionSpecRange[] {
        return [
            {
                id: "center",
                values: {default: 0.05, min: -0.08, max: 1, step: 0.01},
                option_type: "range",
                text: "Center force strength",
            },
            {
                id: "charge",
                values: {default: -300, min: -1000, max: 50, step: 1},
                option_type: "range",
                text: "Repulsion force leaf",
            },
            {
                id: "charge_aggregator",
                values: {default: -300, min: -1000, max: 50, step: 1},
                option_type: "range",
                text: "Repulsion force branch",
            },
            {
                id: "link_distance",
                values: {default: 30, min: -10, max: 300, step: 1},
                option_type: "range",
                text: "Link distance leaf",
            },
            {
                id: "link_distance_aggregator",
                values: {default: 30, min: -10, max: 300, step: 1},
                option_type: "range",
                text: "Link distance branch",
            },
            {
                id: "link_strength",
                values: {default: 0.3, min: 0, max: 2, step: 0.01},
                option_type: "range",
                text: "Link strength",
            },
            {
                id: "collide",
                values: {default: 15, min: 0, max: 150, step: 1},
                option_type: "range",
                text: "Collision box leaf",
            },
            {
                id: "collision_force_aggregator",
                values: {default: 15, min: 0, max: 150, step: 1},
                option_type: "range",
                text: "Collision box branch",
            },
        ];
    }
}
