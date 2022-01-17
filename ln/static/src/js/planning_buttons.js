odoo.define("ln.planning_confirm_gantt_view_button", function (require) {
  "use strict";

  var GanttController = require("@planning/js/planning_gantt_controller")[Symbol.for("default")];

  GanttController.include({
      events: Object.assign({}, GanttController.prototype.events, {
        "click .o_button_send_to_confirm": function (ev) {
          var self = this;
          self.do_action({
            name: "Envoyer les slots à confirmer",
            type: "ir.actions.act_window",
            res_model: "ln.planning.confirm",
            target: "new",
            views: [[false, "form"]],
            context: { is_modal: true },
          });
        },
      }),
      buttonTemplateName: "PlanningGanttView.buttons",
    });
});