var OrderdSelectBox = {
    cache: new Object(),
    init: function(id) {
        var box = document.getElementById(id);
        var node;
        
        OrderdSelectBox.cache[id] = new Array();
        var cache = OrderdSelectBox.cache[id];
        for (var i = 0; (node = box.options[i]); i++) {
            OrderdSelectBox.add_to_cache(id, node);
        }
    },
    redisplay: function(id) {
        // Repopulate HTML select box from cache
        var box = document.getElementById(id);
        box.options.length = 0; // clear all options
        for (var i = 0, j = OrderdSelectBox.cache[id].length; i < j; i++) {
            var node = OrderdSelectBox.cache[id][i];
            if (node.displayed) {
                box.options[box.options.length] = new Option(node.text, node.value, false, false);
            }
        }
    },
    filter: function(id, text) {
        // Redisplay the HTML select box, displaying only the choices containing ALL
        // the words in text. (It's an AND search.)
        var tokens = text.toLowerCase().split(/\s+/);
        var node, token;
        for (var i = 0; (node = OrderdSelectBox.cache[id][i]); i++) {
            node.displayed = 1;
            for (var j = 0; (token = tokens[j]); j++) {
                if (node.text.toLowerCase().indexOf(token) == -1) {
                    node.displayed = 0;
                }
            }
        }
        OrderdSelectBox.redisplay(id);
    },
    delete_from_cache: function(id, value) {
        var node, delete_index = null;
        for (var i = 0; (node = OrderdSelectBox.cache[id][i]); i++) {
            if (node.value == value) {
                delete_index = i;
                break;
            }
        }
        var j = OrderdSelectBox.cache[id].length - 1;
        for (var i = delete_index; i < j; i++) {
            OrderdSelectBox.cache[id][i] = OrderdSelectBox.cache[id][i+1];
        }
        OrderdSelectBox.cache[id].length--;
    },
    add_to_cache: function(id, option) {
      
        var order = 0;
        if( option.getAttribute('data-sort-value') ) {
          order = parseInt( option.getAttribute('data-sort-value') );
        };
        
        OrderdSelectBox.cache[id].push({value: option.value, text: option.text, displayed: 1, order: order });
        
        // Re-order on sort-order-value (every time)
        OrderdSelectBox.cache[id].sort(function(a, b){
          return a.order - b.order;
        });
    },
    cache_contains: function(id, value) {
        // Check if an item is contained in the cache
        var node;
        for (var i = 0; (node = OrderdSelectBox.cache[id][i]); i++) {
            if (node.value == value) {
                return true;
            }
        }
        return false;
    },
    move: function(from, to) {
        var from_box = document.getElementById(from);
        var to_box = document.getElementById(to);
        var option;

        // Remove sort-order-value before move:
        for (var i = 0; (option = OrderdSelectBox.cache[to][i]); i++) {
          option.order = 0;
        }

        for (var i = 0; (option = from_box.options[i]); i++) {
            if (option.selected && OrderdSelectBox.cache_contains(from, option.value)) {
                //OrderdSelectBox.add_to_cache(to, {value: option.value, text: option.text, displayed: 1});
                OrderdSelectBox.add_to_cache(to, option);
                OrderdSelectBox.delete_from_cache(from, option.value);
            }
        }
        OrderdSelectBox.redisplay(from);
        OrderdSelectBox.redisplay(to);
    },
    move_all: function(from, to) {
        var from_box = document.getElementById(from);
        var to_box = document.getElementById(to);
        var option;
        
        for (var i = 0; (option = from_box.options[i]); i++) {
            if (OrderdSelectBox.cache_contains(from, option.value)) {
                //OrderdSelectBox.add_to_cache(to, {value: option.value, text: option.text, displayed: 1});
                OrderdSelectBox.add_to_cache(to, option);
                OrderdSelectBox.delete_from_cache(from, option.value);
            }
        }
        OrderdSelectBox.redisplay(from);
        OrderdSelectBox.redisplay(to);
    },
    sort: function(id) {
        OrderdSelectBox.cache[id].sort( function(a, b) {
            a = a.text.toLowerCase();
            b = b.text.toLowerCase();
            try {
                if (a > b) return 1;
                if (a < b) return -1;
            }
            catch (e) {
                // silently fail on IE 'unknown' exception
            }
            return 0;
        } );
    },
    select_all: function(id) {
        var box = document.getElementById(id);
        for (var i = 0; i < box.options.length; i++) {
            box.options[i].selected = 'selected';
        }
    }
}
