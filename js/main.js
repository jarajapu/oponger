(function(){

    $(function() {

        // Score validation functions
        function is_valid_score(score) {
            return 0 <= score && score < 100;
        }

        function is_int(score) {
            return Number(score) === parseInt(score);
        }

        function is_min_points_to_win(score_1, score_2) {
            return score_1 >= 21 || score_2 >= 21;
        }

        function is_min_spread(score_1, score_2) {
            return Math.abs(score_1 - score_2) >= 2;
        }

        // Attach dialog to complete game link
        $('.complete-game').click(function(){
            $('#complete-game-wrapper').dialog({
                closeText: 'hide',
                draggable: false,
                modal: true,
                resizable: false,
                width: 500
            });
        });

        // Attach form validation to all profile-update forms
        $('#profile-update-form').submit(function() {

            // Get all of the input values
            var $inputs = $(':input', this);
            var values = {};
            $inputs.each(function() {
                values[this.name] = $(this).val();
            });

            values.pseudonym = values.pseudonym.trim()

            if(!values.pseudonym) {
                $('.error', this).html("You've gotta have a pseudonym.");
                return false;
            }

            if(values.pseudonym.length > 15) {
                $('.error', this).html("Please keep your pseudonym up to 15 characters long.");
                return false;
            }

            return true;
        });

    });

})();
