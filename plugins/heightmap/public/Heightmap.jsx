import L from 'leaflet';
import ReactDOM from 'ReactDOM';
import React from 'react';
import PropTypes from 'prop-types';
import './Heightmap.scss';
import HeightmapPabel from './HeightmapPanel';

class HeightmapButton extends React.Component {
  static propTypes = {
    tasks: PropTypes.object.isRequired,
    map: PropTypes.object.isRequired
  }

  constructor(props){
    super(props);

    this.state = {
        showPanel: false
    };
  }

  handleOpen = () => {
    this.setState({showPanel: true});
  }

  handleClose = () => {
    this.setState({showPanel: false});
  }

  render(){
    const { showPanel } = this.state;

    return (<div className={showPanel ? "open" : ""}>
        <a href="javascript:void(0);" 
            onClick={this.handleOpen} 
            className="leaflet-control-heightmap-button leaflet-bar-part theme-secondary"></a>
        <HeightmapPabel map={this.props.map} isShowed={showPanel} tasks={this.props.tasks} onClose={this.handleClose} />
    </div>);
  }
}

export default L.Control.extend({
    options: {
        position: 'topright'
    },

    onAdd: function (map) {
        var container = L.DomUtil.create('div', 'leaflet-control-heightmap leaflet-bar leaflet-control');
        L.DomEvent.disableClickPropagation(container);
        ReactDOM.render(<HeightmapButton map={this.options.map} tasks={this.options.tasks} />, container);

        return container;
    }
});

