PluginsAPI.Map.willAddControls([
    	'labels/build/Labels.js',
    	'labels/build/Labels.css'
	], function(args, Labels){
	var tasks = [];
	for (var i = 0; i < args.tiles.length; i++){
		tasks.push(args.tiles[i].meta.task);
	}

	// TODO: add support for map view where multiple tasks are available?
	if (tasks.length === 1){
		args.map.addControl(new Labels({map: args.map, tasks: tasks}));
	}
});
