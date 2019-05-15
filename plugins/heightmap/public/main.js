PluginsAPI.Map.willAddControls([
    	'heightmap/build/Heightmap.js',
    	'heightmap/build/Heightmap.css'
	], function(args, Heightmap){
	var tasks = [];
	for (var i = 0; i < args.tiles.length; i++){
		tasks.push(args.tiles[i].meta.task);
	}

	// TODO: add support for map view where multiple tasks are available?
	// if (tasks.length === 1){
		args.map.addControl(new Heightmap({map: args.map, tasks: tasks}));
	// }
});
