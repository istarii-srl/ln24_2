/** @odoo-module **/

import PlanningView from 'planning.calendar_frontend';

PlanningView.include({
    // override popup of calendar
    eventFunction: function (calEvent) {
        const planningToken = $('.planning_token').attr('value');
        const employeeToken = $('.employee_token').attr('value');
        $(".modal-title").text(calEvent.event.title);
        $(".modal-header").css("background-color", calEvent.event.backgroundColor);
        $("#start").text(moment(calEvent.event.start).format("YYYY-MM-DD hh:mm A"));
        $("#stop").text(moment(calEvent.event.end).format("YYYY-MM-DD hh:mm A"));
        $("#alloc_hours").text(calEvent.event.extendedProps.alloc_hours);
        $("#role").text(calEvent.event.extendedProps.role);
        if (calEvent.event.extendedProps.alloc_perc !== 100) {
            $("#alloc_perc_value").text(calEvent.event.extendedProps.alloc_perc);
            $("#alloc_perc").css("display", "");
        } else {
            $("#alloc_perc").css("display", "none");
        }

        if (calEvent.event.extendedProps.role) {
            $("#role").prev().css("display", "");
            $("#role").text(calEvent.event.extendedProps.role);
            $("#role").css("display", "");
        } else {
            $("#role").prev().css("display", "none");
            $("#role").css("display", "none");
        }
        if (calEvent.event.extendedProps.note) {
            $("#note").prev().css("display", "");
            $("#note").text(calEvent.event.extendedProps.note);
            $("#note").css("display", "");
        } else {
            $("#note").prev().css("display", "none");
            $("#note").css("display", "none");
        }
        $("#allow_self_unassign").text(calEvent.event.extendedProps.allow_self_unassign);
        if (
            calEvent.event.extendedProps.allow_self_unassign
            && !calEvent.event.extendedProps.is_unassign_deadline_passed
            ) {
            document.getElementById("dismiss_shift").style.display = "block";
        } else {
            document.getElementById("dismiss_shift").style.display = "none";
        }
        $("#modal_action_dismiss_shift").attr("action", "/planning/" + planningToken + "/" + employeeToken + "/unassign/" + calEvent.event.extendedProps.slot_id);
        $("#ln_modal_confirm").attr("action", "/confirm/" + planningToken + "/" + employeeToken + "/assign/" + calEvent.event.extendedProps.slot_id);
        $("#ln_modal_refuse").attr("action", "/confirm/" + planningToken + "/" + employeeToken + "/unassign/" + calEvent.event.extendedProps.slot_id);
        if (calEvent.event.extendedProps.confirm_status == 'confirmed') {
            $("#ln_modal_confirm").css("display", "none")
            $("#ln_modal_refuse").css("display", "none")
        } else {
            $("#ln_modal_confirm").css("display", "block")
            if (calEvent.event.extendedProps.confirm_status == 'refused') {
                $("#ln_modal_refuse").css("display", "none")
            } else {
                $("#ln_modal_refuse").css("display", "block")
            }
        }
        
        $("#fc-slot-onclick-modal").modal("show");
    },
});